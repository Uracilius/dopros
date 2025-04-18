import threading
import time
from datetime import datetime
from network_service import NetworkService
from case_service import CaseService
from repository import CaseRepository
from models import CaseModel
from db import get_db_session
from enums import CaseStatus
import config
import requests


class Orchestrator:
    def __init__(self):
        db_session = next(get_db_session())
        self.case_repository = CaseRepository(db_session)
        self.case_service = CaseService(self.case_repository)
        self.network_service = NetworkService()
        self.network_thread = threading.Thread(
            target=self.network_service.monitor_network,
            args=(self.case_service,),
            daemon=True,
        )

    def create_case(self, case_data):

        if "create_date" in case_data:
            case_data["create_date"] = datetime.fromisoformat(case_data["create_date"])
        if "update_date" in case_data:
            case_data["update_date"] = datetime.fromisoformat(case_data["update_date"])

        case_model = CaseModel(**case_data)
        case_entity = self.case_service.create_new_case(case_model)
        print(f"Case {case_entity.id} created successfully.")
        return case_entity

    def partial_update(self, case_id: int, updated_fields: dict):
        """Updates an existing case, applying only the fields you provide."""
        updated_case = self.case_service.partial_update(case_id, updated_fields)
        if updated_case:
            print(f"Case {case_id} updated successfully.")
        else:
            print(f"Case {case_id} not found or update failed.")
        return updated_case

    def has_internet_check(self, url: str) -> bool:
        """Return True if an HTTP GET request to `url` succeeds, otherwise False."""
        try:
            response = requests.get(url, timeout=3)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def fetch_case_list(self, api_url=config.SERVER_API_URL):
        try:
            response = requests.get(api_url + "/getCase", timeout=5)
            response.raise_for_status()
            data = response.json()
            print("Fetched case list:", data)

            if data:
                self.create_case(data)
        except requests.RequestException as e:
            print(f"Error fetching case list: {e}")

    def main(self):
        last_fetch_time = 0
        while True:
            if self.has_internet_check(config.NETWORK_CHECK_URL):
                if (time.time() - last_fetch_time) >= config.FETCH_INTERVAL:
                    self.fetch_case_list()
                    last_fetch_time = time.time()
            time.sleep(config.CHECK_INTERVAL)


if __name__ == "__main__":
    orchestrator = Orchestrator()

    orchestrator.main()
