import argparse
import asyncio
import logging
import os
import sys

from automation_server_client import AutomationServer, Workqueue, WorkItemError, Credential
from nexus_database_client import NexusDatabaseClient
from kmd_nexus_client import NexusClientManager
from odk_tools.tracking import Tracker

from process.config import load_excel_mapping, get_excel_mapping

nexus: NexusClientManager
nexus_database_client: NexusDatabaseClient
tracker: Tracker

proces_navn = "Tilføjelse af primær organisation hos ændrede borgere"


async def populate_queue(workqueue: Workqueue):
    logger = logging.getLogger(__name__)

    logger.info("Hello from populate workqueue!")

    regler = get_excel_mapping()

    for organisation in regler["Organisationer"]:
        borgere = nexus_database_client.get_patients_with_recently_assigned_professionals_by_organisation_name(
            organisation, 30
        )
        for borger in borgere:
            workqueue.add_item(
                data={"cpr": borger["cpr"], 
                    "organisation": organisation},
                reference=borger["cpr"],
            )



async def process_workqueue(workqueue: Workqueue):
    logger = logging.getLogger(__name__)

    logger.info("Hello from process workqueue!")

    for item in workqueue:
        with item:
            data = item.data  # Item data deserialized from json as dict
 
            try:
                # Process the item here
                borger = nexus.borgere.hent_borger(data["cpr"])
                borgers_organisationer = nexus.organisationer.hent_organisationer_for_borger(borger)

                # Find organisationen, der skal opdateres.
                organisation_til_opdatering = next(
                    (
                        item
                        for item in borgers_organisationer
                        if item["organization"]["name"] == data["organisation"]
                    ),
                    None,
                )
                # Hvis organisationen allerede er primær, så stopper vi her.
                if organisation_til_opdatering["primaryOrganization"]:
                    continue

                nexus.organisationer.opdater_borger_organisations_relation(
                    organisation_til_opdatering,
                    None,
                    True
                )
                
                tracker.track_task(
                    proces_navn
                )
                pass
            except WorkItemError as e:
                # A WorkItemError represents a soft error that indicates the item should be passed to manual processing or a business logic fault
                logger.error(f"Error processing item: {data}. Error: {e}")
                item.fail(str(e))


if __name__ == "__main__":
    ats = AutomationServer.from_environment()

    workqueue = ats.workqueue()

         # Parse command line arguments
    parser = argparse.ArgumentParser(description=proces_navn)
    parser.add_argument(
        "--excel-file",
        default="./Regler.xlsx",
        help="Path to the Excel file containing mapping data (default: ./Regler.xlsx)",
    )
    parser.add_argument(
        "--queue",
        action="store_true",
        help="Populate the queue with test data and exit",
    )
    args = parser.parse_args()

    # Validate Excel file exists
    if not os.path.isfile(args.excel_file):
        raise FileNotFoundError(f"Excel file not found: {args.excel_file}")

    # Load POF mapping data once on startup
    load_excel_mapping(args.excel_file)

    # Initialize external systems for automation here..
    nexus_credential = Credential.get_credential("KMD Nexus - produktion")
    nexus_database_credential = Credential.get_credential("KMD Nexus - database")
    tracking_credential = Credential.get_credential("Odense SQL Server")

    nexus = NexusClientManager(
        client_id=nexus_credential.username,
        client_secret=nexus_credential.password,
        instance=nexus_credential.data["instance"],
    )    
    
    nexus_database_client = NexusDatabaseClient(
        host=nexus_database_credential.data["hostname"],
        port=nexus_database_credential.data["port"],
        user=nexus_database_credential.username,
        password=nexus_database_credential.password,
        database=nexus_database_credential.data["database_name"],
    )

    tracker = Tracker(
        username=tracking_credential.username, 
        password=tracking_credential.password
    )

    # Queue management
    if "--queue" in sys.argv:
        workqueue.clear_workqueue("new")
        asyncio.run(populate_queue(workqueue))
        exit(0)

    # Process workqueue
    asyncio.run(process_workqueue(workqueue))
