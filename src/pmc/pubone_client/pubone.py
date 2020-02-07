from typing import Union
from pmc.restapi_client import RestApi, session as s
import re
from itertools import chain

PUBONE_EP = (
    "http://pubone.linkerd.ncbi.nlm.nih.gov"
    # do not forget http_proxy='linkerd:4140'.
    # http://pubone.service.l5d.query.aws-prod.consul.ncbi.nlm.nih.gov/
    # http://pubone.service.l5d.query.aws-dev.consul.ncbi.nlm.nih.gov/
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
        _ = (
            "`{_name}` must be a positive integer value,"
            "{repr(_value)} provided instead."
        )

        try:
            if value is not None:
                value = int(value)
                if value <= 0:
                    raise ValueError(_.format(value=value, name=name))
        except (ValueError, TypeError):
            raise ValueError(_(value, name))

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
        self._api = RestApi(ep=ep, session=session, debug=debug)

        self._pmid = None
        self._pmcid = None
        self._doi = None

        self._ep = ep
        self._session = session
        self._logger = logger
        self._debug = debug

    def valid(self, pmid: int = None, pmcid: int = None) -> bool:
        pmid = self._validate_id(pmid, "pmid")
        pmcid = self._validate_id(pmcid, "pmcid")
        if pmid is None and pmcid is None:
            raise ValueError("At least one of `pmid` or `pmcid` must be specified.")

        resource = ",".join(
            [
                i
                for i in [
                    pmid and f"pubmed_{pmid}" or None,
                    pmcid and f"pmc_{pmcid}" or None,
                ]
                if i
            ]
        )

        resource = getattr(self._api.lojson, resource)
        response = resource.get()
        data = response.data

        # from devtools import debug as d
        # print(f"data={d.format(data)}")

        if not isinstance(data, (dict, list, tuple)) or len(data) != 1:
            return False

        data_0 = next(iter(data), {})  # get first item of the list `data` or {}
        if not data_0:
            return False

        _pmcid_raw = data_0.get("pmcid")
        _pmid_raw = data_0.get("id")

        self._pmcid = _pmcid = self._eval_pmcid(_pmcid_raw)
        self._pmid = _pmid = self._eval_pmid(_pmid_raw)
        self._doi = data_0.get("doi", None)

        return (
            (pmid == _pmid and _pmcid == pmcid)
            or (pmid is None and pmcid == _pmcid)
            or (pmid == _pmid and pmcid is None)
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
        self._api = RestApi(ep=ep, session=session, debug=debug)

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
            raise ValueError(f"Both `pmids` and `pmcids` are not deined.")

        self._validate_ids(pmids, "pmids", "pmid")
        self._validate_ids(pmcids, "pmcids", "pmcid")

        results = []
        for params_group in self._params_group_gen(pmids, pmcids):
            resource = getattr(self._api, api_name)(params_group)
            response = resource.get()
            if (
                response.data is not None
                and isinstance(response.data, list)
                and len(response.data) > 0
            ):
                results += response.data
        return results

    def lojson(self, pmids=None, pmcids=None):
        return self._api_generic("lojson", pmids, pmcids)

    def citjson(self, pmids=None, pmcids=None):
        return self._api_generic("citjson", pmids, pmcids)

    def csljson(self, pmids=None, pmcids=None):
        return self._api_generic("csljson", pmids, pmcids)
