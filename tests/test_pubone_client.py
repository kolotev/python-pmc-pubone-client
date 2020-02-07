import pytest
from pmc.pubone_client import PubOneValidator, PubOneApi, WebServiceFtsType, PUBONE_EP


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
    assert pubone.valid(pmid=pmid) is True
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
    assert pubone.valid(pmcid=pmcid) is True
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
    assert pubone.valid(pmid=pmid, pmcid=pmcid) is True
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
    assert pubone.valid(pmcid=pmcid) is True
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

    with pytest.raises(ValueError, match=r"Both .* are not deined."):
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
    results = pubone.lojson(pmids=list(range(1, 300)))

    assert 299 >= len(results) >= 290
