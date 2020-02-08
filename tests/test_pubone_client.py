import pytest
from pmc.pubone_client import PubOneValidator, PubOneApi, WebServiceFtsType, PUBONE_EP
from pmc.pubone_client import exceptions as ex
from itertools import chain


def test_init():
    """
    Test ``instantiate an instance`` functionality.
    """
    pubone = PubOneValidator()
    assert pubone

    pubone = PubOneApi()
    assert pubone


validate_pmid_10 = [
    {"id": "10", "pmcid": "PMC5922622"},
]

validate_pmcid_13901 = [
    {"id": "11250747", "pmcid": "PMC13901"},
]

validate_versioned_pmcid = [
    {"id": "30175244", "pmcid": "PMC6081977.3"},
]

api_results = [
    {"k1": "v1_1", "k2": "v2_1"},
    {"k1": "v1_2", "k2": "v2_2"},
    {"k1": "v1_3", "k2": "v2_3"},
]

headers = {"Content-Type": "application/json"}


def test_validate_pmid(requests_mock):
    """
    Test ``validate pmvalidateid_10y.
    """
    pmid = 10
    json = validate_pmid_10
    requests_mock.get(
        PUBONE_EP + f"/lojson/pubmed_{pmid}", json=json, headers=headers,
    )
    pubone = PubOneValidator(session=WebServiceFtsType())
    assert pubone.validate(pmid=pmid) is True
    assert pubone.pmid == pmid


def test_validate_pmcid(requests_mock):
    """
    Test ``validate pmcid`` functionality.
    """
    pmcid = 13901
    json = validate_pmcid_13901
    requests_mock.get(
        PUBONE_EP + f"/lojson/pmc_{pmcid}", json=json, headers=headers,
    )
    pubone = PubOneValidator(session=WebServiceFtsType())
    assert pubone.validate(pmcid=pmcid) is True
    assert pubone.pmcid == pmcid


def test_validate_pmid_and_pmcid(requests_mock):
    """
    Test ``validate pmid and pmcid`` functionality
    """
    pmid = 10
    pmcid = 5922622
    json = validate_pmid_10
    requests_mock.get(
        PUBONE_EP + f"/lojson/pubmed_{pmid},pmc_{pmcid}", json=json, headers=headers,
    )
    pubone = PubOneValidator(session=WebServiceFtsType())
    assert pubone.validate(pmid=pmid, pmcid=pmcid) is True
    assert pubone.pmcid == pmcid
    assert pubone.pmid == pmid


def test_validate_versioned_pmcid(requests_mock):
    """
    Test ``validate versioned pmcid`` functionality.
    In context of bug on pubone side.
    """
    pmcid = 6081977
    json = validate_versioned_pmcid
    requests_mock.get(
        PUBONE_EP + f"/lojson/pmc_{pmcid}", json=json, headers=headers,
    )

    pubone = PubOneValidator(session=WebServiceFtsType())
    assert pubone.validate(pmcid=pmcid) is True
    assert pubone.pmcid == pmcid


@pytest.mark.parametrize("api_name", ["lojson", "citjson", "csljson"])
def test_apis(requests_mock, api_name):
    """
    Test ``JSON PubOne API`` functionality.
    """
    json = api_results
    requests_mock.get(
        PUBONE_EP + f"/{api_name}/pubmed_1,pmc_1,pmc_2", json=json, headers=headers,
    )

    pubone = PubOneApi(session=WebServiceFtsType())
    results = getattr(pubone, api_name)(pmids=[1], pmcids=(1, 2))

    assert len(results) == 3
    assert results == api_results


def test_ids_exceptions():
    """
    Test ``exceptions`` functionality.
    """
    pubone = PubOneApi(session=WebServiceFtsType())

    with pytest.raises(ValueError, match=r"Both .* are not defined."):
        pubone.lojson()

    with pytest.raises(ValueError, match=r"must be list or tuple"):
        pubone.lojson(pmids=1234)

    with pytest.raises(ValueError, match=r"must be list or tuple"):
        pubone.lojson(pmcids=1234)


def test_multiple_requests_call():
    """
    Test ``real call to pubone api with long list of items`` functionality.
    """
    proxies = {
        "http": "linkerd:4140",
    }
    session = WebServiceFtsType()
    session.proxies = proxies

    pubone = PubOneApi(session=session)
    results = pubone.lojson(pmids=list(range(1, 301)))

    assert len(results) == 300


def _prep_mock(requests_mock, pmid, pmcid, outcome, mocked_json):

    json = []

    if mocked_json is not None:
        json = mocked_json

    elif outcome is not ValueError:
        json = [{}]
        for i in list(
            chain(
                map(lambda i: {"id": str(i)}, pmid and [pmid] or []),
                map(lambda i: {"pmcid": f"PMC{i}"}, pmcid and [pmcid] or []),
            )
        ):
            json[0].update(i)

    resource = ",".join(
        chain(
            map(lambda i: f"pubmed_{i}", pmid and [pmid] or []),
            map(lambda i: f"pmc_{i}", pmcid and [pmcid] or []),
        )
    )

    requests_mock.get(
        PUBONE_EP + f"/lojson/{resource}", json=json, headers=headers,
    )


@pytest.mark.parametrize(
    "case,pmid,pmcid,outcome,mocked_json",
    [
        ("case_0.0", None, None, ValueError, None),
        ("case_0.1", "abc", None, ValueError, None),
        ("case_0.2", None, "xyz", ValueError, None),
        ("case_0.3", "abc", "xyz", ValueError, None),
        ("case_0.4", -1, None, ValueError, None),
        ("case_0.5", None, 0, ValueError, None),
        ("case_1", 10, 5922622, True, None),
        (
            "case_2",
            10,
            13901,
            ex.PmidPmcidMismatch,
            [{"id": "10", "pmcid": "PMC5922622"}, {"id": "", "pmcid": "PMC13901"}],
        ),
        ("case_3.1", 10, 10, ex.PmcidAbsent, [{"id": "10", "pmcid": "PMC5922622"}]),
        ("case_3.2", 1053, 1, ex.PmcidAbsent, [{"id": "1053"}]),
        ("case_4", 10, None, True, [{"id": "10", "pmcid": "PMC5922622"}]),
        (
            "case_5",
            1054,
            13901,
            ex.PmidAbsent,
            [{"id": "11250747", "pmcid": "PMC13901"}],
        ),
        ("case_6", 1054, 10, ex.PmidPmcidAbsent, []),
        ("case_7", 1054, None, ex.PmidAbsent, []),
        ("case_8", None, 13901, True, [{"id": "11250747", "pmcid": "PMC13901"}]),
        ("case_9", None, 10, ex.PmcidAbsent, []),
    ],
)
def test_case(requests_mock, case, pmid, pmcid, outcome, mocked_json):
    """
    Test ``cases of PubOne API`` functionality.
    """
    # prepare mocked response
    _prep_mock(requests_mock, pmid, pmcid, outcome, mocked_json)

    #
    pubone = PubOneValidator(session=WebServiceFtsType())

    if isinstance(outcome, bool):
        assert pubone.validate(pmid=pmid, pmcid=pmcid) is True
    elif isinstance(outcome, type):
        with pytest.raises(outcome):
            pubone.validate(pmid=pmid, pmcid=pmcid) is not True
    else:
        raise RuntimeError(
            f"Unexpected end if test case={case} pmid={pmid} "
            f"pmcid={pmcid} outcome={outcome}"
        )
