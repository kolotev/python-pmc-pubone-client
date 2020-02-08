class BaseException(Exception):
    default_error_message = "PubOne error"

    def __init__(self, **kwargs):
        super().__init__(self.default_error_message.format(**kwargs))


class PmidAbsent(BaseException):
    """Exception to indicate, that a given pmid
    does not exist in PubOne."""

    default_error_message = "pmid=`{pmid}` is missing in PubOne"

    def __init__(self, pmid):
        self.pmid = pmid
        super().__init__(pmid=pmid)


class PmcidAbsent(BaseException):
    """Exception to indicate, that a given pmcid
    does not exist in PubOne."""

    default_error_message = "pmcid=`{pmcid}` is missing in PubOne."

    def __init__(self, pmcid):
        self.pmcid = pmcid
        super().__init__(pmcid=pmcid)


class PmidPmcidAbsent(BaseException):
    """Exception to indicate, that both pmid and pmcid
    do not exist in PubOne."""

    default_error_message = (
        "pmid=`{pmid}` and pmcid=`{pmcid}` are both missing in PubOne."
    )

    def __init__(self, pmid, pmcid):
        self.pmid = pmid
        self.pmcid = pmcid
        super().__init__(pmid=pmid, pmcid=pmcid)


class PmidPmcidMismatch(BaseException):
    """Exception to indicate, that a given pmid and pmcid
    do not match/correspond to the same article in PubOne."""

    default_error_message = (
        "pmid=`{pmid}` and pmcid=`{pmcid}` are not matching "
        "to the same article in PubOne."
    )

    def __init__(self, pmid, pmcid):
        self.pmid = pmid
        self.pmcid = pmcid
        super().__init__(pmid=pmid, pmcid=pmcid)


class PubOneServiceFailed(BaseException):
    default_error_message = (
        "PubOne service is faling with the following diagnostics: {exception}"
    )

    def __init__(self, exception):
        super().__init__(exception=exception)
