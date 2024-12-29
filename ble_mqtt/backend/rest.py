import requests
import logging

from getmac import get_mac_address
from backend.filters import FiltersDTO, FilterCriteriaDTO

logger = logging.getLogger(__name__)


class RestClient(object):
    def __init__(self, base_url):
        logger.debug("Init REST Client")
        self.base_url = base_url

    def get_all_machineries(self):
        filters = FiltersDTO([], [], [], "AND")
        response = requests.post(self.base_url + "/machineries/search?unpaged=true", json=vars(filters))

        if response.status_code == 200:
            return response.json()['content']
        
        return []

    def get_user_info(self):
        # get mac address
        # headphone_serial = get_mac_address()
        headphone_serial = "123456789"

        logger.info("Obtain user info by serial: %s", headphone_serial)

        criteria = FilterCriteriaDTO('headphone.serial', "EQUAL", headphone_serial)
        filters = FiltersDTO([], [vars(criteria)], [], "AND")
        
        response = requests.post(
            self.base_url + "/users/search?unpaged=true", json=vars(filters))
        
        if response.status_code == 200:
            content = response.json()['content']
            if len(content) == 1:
                return content[0]
        
        logger.error("Attempt to retrieve user info failed. Please check that the serial [%s] is defined on the backend.", headphone_serial)
        raise Exception()
