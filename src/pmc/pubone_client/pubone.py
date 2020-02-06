from typing import Union
from pmc.restapi_client import RestApi, session as s
import re

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

# we possibly can set longer periods and larger try numbers.


class PubOneClient:
    def __init__(self, ep=PUBONE_EP, session=CmdLineFtsType(), debug=0):
        self._api = RestApi(ep=ep, session=session, debug=debug)
        self._pmid = None
        self._pmcid = None
        self._doi = None

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

    def _eval_pmid(self, pmid_raw):
        if isinstance(pmid_raw, str):
            return int(pmid_raw)

    def _eval_pmcid(self, pmcid_raw):
        if isinstance(pmcid_raw, str):
            _pmcid_str, _ = re.subn(UNWANTED_CHARS, "", pmcid_raw)
            return int(float(_pmcid_str))

    @property
    def pmid(self):
        return self._pmid

    @property
    def pmcid(self):
        return self._pmcid

    @property
    def doi(self):
        return self._doi


# if __name__ == "__main__":
#     import logging as lg
#
#     LOGGING_FORMAT = "%(levelname)-7s %(asctime)s.%(msecs)03d  %(message)s"
#     lg.basicConfig(format=LOGGING_FORMAT, datefmt="%Y-%m-%dT%H:%M:%S")
#     lg.getLogger().setLevel(level=lg.DEBUG)
#
#     pone = PubOne(debug=3)
#     assert pone.valid(pmcid=1) is False
#     assert pone.valid(pmcid=1) is False
#     assert pone.valid(pmid=40_000_000) is False
#     assert pone.valid(pmid=1) is True
#     assert pone.valid(pmcid=13901) is True
#     assert pone.valid(pmid=1, pmcid=13901) is False
#     assert pone.valid(pmid=11250747, pmcid=13901) is True
