from typing import Union, List
from pmc.restapi_client import RestApi, session as s
import re
from itertools import chain
from . import exceptions as ex
from pmc.restapi_client import exceptions as api_ex

PUBONE_EP = (
    "http://pubone.linkerd.ncbi.nlm.nih.gov"
    # do not forget http_proxy='linkerd:4140'.
    # http://pubone.service. l5d .query.aws-prod.consul.ncbi.nlm.nih.gov/
    # http://pubone.service. l5d .query.aws-dev.consul.ncbi.nlm.nih.gov/
)

# The following Type is suitable for for command-line clients
CmdLineFtsType = s.FtsClassFactory(
    max_tries=10,  # maximum number of tries
    max_time=120,  # maximum time to try.
    max_value=15,  # back.fibo argument - maximum interval between tries
)

# The following Type is suitable for for command-line clients
WebServiceFtsType = s.FtsClassFactory(
    max_time=3,  # maximum time to try.
    max_value=1,  # back.fibo argument - maximum interval between tries
    timeout=(3.2, 2),
)

#
UNWANTED_CHARS = r"[^\d\.]+"


class PubOneBase:
    def _eval_pmid(self, pmid_raw):
        if isinstance(pmid_raw, str):
            return int(pmid_raw)

    def _eval_pmcid(self, pmcid_raw):
        if isinstance(pmcid_raw, str):
            _pmcid_str, _ = re.subn(UNWANTED_CHARS, "", pmcid_raw)
            return int(float(_pmcid_str))

    def _validate_id(self, value: Union[int, str], name: str) -> bool:
        error_message = (
            "`{name}` must be a positive integer value," "`{value}` provided instead."
        )

        try:
            if value is not None:
                value = int(value)
                if value <= 0:
                    raise ValueError(error_message.format(value=value, name=name))
        except (ValueError, TypeError):
            raise ValueError(error_message.format(value=value, name=name))

        return value

    def _validate_ids(self, ids, ids_name, id_name):
        ids_type = type(ids)

        if ids is not None:
            if ids_type not in (list, tuple):
                raise ValueError(
                    f"`{ids_name}` must be list or tuple, {ids_type} supplied instead."
                )
            map(lambda id: self._validate_id(id, id_name), ids)


class PubOneValidator(PubOneBase):
    def __init__(self, ep=PUBONE_EP, session=CmdLineFtsType(), logger=None, debug=0):
        self._api = RestApi(ep=ep, session=session, logger=logger, debug=debug)

        self._ep = ep
        self._session = session
        self._logger = logger
        self._debug = debug

    def _lookup_pubone(self, pmid: int, pmcid: int) -> List[dict]:
        params = [
            pmid and f"pubmed_{pmid}" or None,
            pmcid and f"pmc_{pmcid}" or None,
        ]
        resource_name = ",".join(list(filter(lambda i: i is not None, params)))

        try:
            response = self._api.lojson(resource_name).get()
        except api_ex.HttpServerError as e:
            raise ex.PubOneServiceFailed(e)

        return response.data

    def _validate_item(self, data_item, pmid, pmcid):
        if not isinstance(data_item, dict):
            raise ex.PubOneServiceFailed(
                ValueError(
                    f"PubOne API returned an unexpected record `{data_item}` "
                    f"for the following data pmid={pmid} pmcid={pmcid}, "
                    "contact developer."
                )
            )

        _pmcid_raw = data_item.get("pmcid")
        _pmid_raw = data_item.get("id")
        _pmcid = self._eval_pmcid(_pmcid_raw)
        _pmid = self._eval_pmid(_pmid_raw)
        _doi = data_item.get("doi", None)

        pmid_exists = pmid if pmid is None else pmid == _pmid
        pmcid_exists = pmcid if pmcid is None else pmcid == _pmcid

        # print(f"\npmid={pmid} _pmid={_pmid} pmid_exists={pmid_exists}")
        # print(f"pmid={pmcid} _pmid={_pmcid} pmcid_exists={pmcid_exists}")

        # cases 1, 4, 8
        if (
            (pmid_exists is True and pmcid_exists is True)  # 1
            or (pmid_exists is True and pmcid_exists is None)  # 4
            or (pmid_exists is None and pmcid_exists is True)  # 8
        ):
            self._pmcid = _pmcid
            self._pmid = _pmid
            self._doi = _doi
            return True

        # case 3
        if pmid_exists is True and pmcid_exists is False:  # 3
            raise ex.PmcidAbsent(pmcid)

        # case 5
        if pmid_exists is False and pmcid_exists is True:  # 5
            raise ex.PmidAbsent(pmid)

    def validate(self, pmid: int = None, pmcid: int = None) -> bool:
        """Validates PubMed Id and PMC Id for presence in PubOne service,
        and match to the same article.

        Keyword Arguments:
            pmid {int} -- PubMed Id (default: {None})
            pmcid {int} -- PMC Id (default: {None})

        Returns:
            bool -- True if result of validation is positive.

Case    Outcome             pmid    pmcid    match   #Recs - (from PubOne)
0       ValueError          None    None     -       -
1       True                exists  exists   yes     1
2       PmidPmcidMismatch   exists  exists   no      2
3       PmcidAbsent         exists  absent           1
4       True                exists  None             1
5       PmidAbsent          absent  exists           1
6       PmidPmcidAbsent     absent  absent           0
7       PmidAbsent          absent  None             0
8       True                None    exists           1
9       PmcidAbsent         None    absent           0

        exists = id is not None and id = _id
                 where id is one of pmid or pmcid supplied
                 and _id corresponding identifier received from PubOne.
        absent = not(exists)"""
        self._pmid = None
        self._pmcid = None
        self._doi = None

        # case 0
        if pmid is None and pmcid is None:
            raise ValueError(
                "Both `pmid` and `pmcid` are undefined, "
                "at least one must be provided."
            )

        pmid = self._validate_id(pmid, "pmid")
        pmcid = self._validate_id(pmcid, "pmcid")
        data = self._lookup_pubone(pmid, pmcid)

        # from devtools import debug as d
        # print(f"data={d.format(data)}")

        if not isinstance(data, (list)):
            raise ex.PubOneServiceFailed(
                ValueError(
                    f"A list of records was expected from PubOne, "
                    f"data={data} was received instead."
                )
            )

        # case 2
        if len(data) == 2 and pmid is not None and pmcid is not None:
            raise ex.PmidPmcidMismatch(pmid, pmcid)

        # cases 1, 4, 8 and 3, 5
        elif len(data) == 1:
            data_1 = next(iter(data), {})  # get 1st item of the list `data` or {}
            return self._validate_item(data_1, pmid, pmcid)

        # cases 6, 7, 9
        elif len(data) == 0:
            if pmid is not None and pmcid is not None:  # 6
                raise ex.PmidPmcidAbsent(pmid, pmcid)
            if pmid is not None and pmcid is None:  # 7
                raise ex.PmidAbsent(pmid)
            if pmid is None and pmcid is not None:  # 9
                raise ex.PmcidAbsent(pmcid)

        raise RuntimeError(
            "PubOne client experienced unexpected outcome, contact developer "
            "with following data pmid={pmid} pmcid={pmcid} data={data}."
        )

    @property
    def pmid(self):
        return self._pmid

    @property
    def pmcid(self):
        return self._pmcid

    @property
    def doi(self):
        return self._doi


class PubOneApi(PubOneBase):
    def __init__(self, ep=PUBONE_EP, session=CmdLineFtsType(), logger=None, debug=0):
        self._api = RestApi(ep=ep, session=session, logger=logger, debug=debug)

        self._ep = ep
        self._session = session
        self._logger = logger
        self._debug = debug

    def _params_group_gen(self, pmids=None, pmcids=None):
        params_gen = chain(
            map(lambda i: f"pubmed_{i}", pmids or []),
            map(lambda i: f"pmc_{i}", pmcids or []),
        )

        s = ""
        for param in params_gen:
            s += param + ","
            if len(s) >= 2000:
                yield s.rstrip(",")
                s = ""

        if len(s) > 0:
            yield s.rstrip(",")

    def _api_generic(self, api_name, pmids=None, pmcids=None):

        if pmids is None and pmcids is None:
            raise ValueError(f"Both `pmids` and `pmcids` are not defined.")

        self._validate_ids(pmids, "pmids", "pmid")
        self._validate_ids(pmcids, "pmcids", "pmcid")

        results = []
        for params_group in self._params_group_gen(pmids, pmcids):
            resource = getattr(self._api, api_name)(params_group)
            response = resource.get()

            data = response.data
            data = [data] if isinstance(data, dict) else data

            if data is not None and isinstance(data, list) and len(data) > 0:
                results += data

        return results

    def lojson(self, pmids=None, pmcids=None):
        return self._api_generic("lojson", pmids, pmcids)

    def citjson(self, pmids=None, pmcids=None):
        return self._api_generic("citjson", pmids, pmcids)

    def csljson(self, pmids=None, pmcids=None):
        return self._api_generic("csljson", pmids, pmcids)
