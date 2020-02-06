from pmc.pubone_client import PubOneClient, WebServiceFtsType, PUBONE_EP


def test_init():
    """
    Test ``instantiate an instance`` functionality.
    """
    pubone = PubOneClient()
    assert pubone


lojson_pmid_10 = [
    {"id": "10", "pmcid": "PMC5922622"},
]

lojson_pmcid_13901 = [
    {"id": "11250747", "pmcid": "PMC13901"},
]

lojson_versioned_pmcid = [
    {"id": "30175244", "pmcid": "PMC6081977.3"},
]


headers = {"Content-Type": "application/json"}


def test_pmid(requests_mock):
    """
    Test ``validate pmid`` functionality.
    """
    pmid = 10
    json = lojson_pmid_10
    requests_mock.get(
        PUBONE_EP + f"/lojson/pubmed_{pmid}", json=json, headers=headers,
    )
    pubone = PubOneClient(session=WebServiceFtsType())
    assert pubone.valid(pmid=pmid) is True
    assert pubone.pmid == pmid


def test_pmcid(requests_mock):
    """
    Test ``validate pmcid`` functionality.
    """
    pmcid = 13901
    json = lojson_pmcid_13901
    requests_mock.get(
        PUBONE_EP + f"/lojson/pmc_{pmcid}", json=json, headers=headers,
    )
    pubone = PubOneClient(session=WebServiceFtsType())
    assert pubone.valid(pmcid=pmcid) is True
    assert pubone.pmcid == pmcid


def test_pmid_and_pmcid(requests_mock):
    """
    Test ``validate pmid and pmcid`` functionality.
    """
    pmid = 10
    pmcid = 5922622
    json = lojson_pmid_10
    requests_mock.get(
        PUBONE_EP + f"/lojson/pubmed_{pmid},pmc_{pmcid}", json=json, headers=headers,
    )
    pubone = PubOneClient(session=WebServiceFtsType())
    assert pubone.valid(pmid=pmid, pmcid=pmcid) is True
    assert pubone.pmcid == pmcid
    assert pubone.pmid == pmid


def test_versioned_pmcid(requests_mock):
    """
    Test ``validate versioned pmcid`` functionality.
    In context of bug on pubone side.
    """
    pmcid = 6081977
    json = lojson_versioned_pmcid
    requests_mock.get(
        PUBONE_EP + f"/lojson/pmc_{pmcid}", json=json, headers=headers,
    )

    pubone = PubOneClient(session=WebServiceFtsType())
    assert pubone.valid(pmcid=pmcid) is True
    assert pubone.pmcid == pmcid
