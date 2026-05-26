from .sap import parse_sap_file
from .travel import parse_travel_file
from .utility import parse_utility_file

PARSERS = {
    "sap": parse_sap_file,
    "utility": parse_utility_file,
    "travel": parse_travel_file,
}
