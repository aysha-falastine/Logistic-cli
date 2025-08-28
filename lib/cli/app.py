from lib.db.database import SessionLocal
from lib.db.models import Truck, FuelLog, Driver
from datetime import date, datetime

# ---- LIST ----
def list_trucks(session):
    trucks = Truck.get_all(session) #helper from CRUDMixin in models.py
    if not trucks:
        print("No trucks found.")
        return
    for t in trucks:
        print(f"[{t.id}] {t.plate} | {t.capacity_liters} L | {t.status}") # display truck info in a readable format

# ---- CREATE ----
def create_truck(session):
    plate = input("Plate: ").strip() #ask user for truck details
    cap_raw = input("Capacity (L): ").strip() #.strip() removes extra spaces
    status = (input("Status (active/maintenance/retired): ").strip() or "active").lower() #default to active if blank

    try:
        capacity = float(cap_raw) #convert capacity input into number
    except ValueError:
        print("Capacity must be a number.") #invalid input show error and stops
        return

    try:
        t = Truck.create(session, plate=plate, capacity_liters=capacity, status=status)
        print(f"Created truck {t.plate} (id={t.id})") 
    except Exception as e:
        session.rollback() #undo any changes if error occurs
        print("Error:", e)

# ---- DELETE ----
def delete_truck(session):
    # show current trucks first
    list_trucks(session)
    try:
        id_str = input("Enter truck id to delete: ").strip() #ask user for truck ID to delete and remove extra spaces
        id_ = int(id_str)
    except ValueError:
        print("Invalid id (must be a number).")
        return

    ok = Truck.delete(session, id_)
    print("Deleted." if ok else "Truck not found.") #this is for confirmation whether truck was deleted or not found

def find_truck_by_plate(session):
    plate = input("Enter plate to search: ").strip().upper() #for searching truck by plate number
    if not plate:
        print("Plate cannot be empty.")
        return
    t = session.query(Truck).filter(Truck.plate == plate).first()
    if t:
        print(f"Found: [{t.id}] {t.plate} | {t.capacity_liters} L | {t.status}")
    else:
        print("No match.")
# *--- VIEW FUEL LOGS FOR A TRUCK ----
def view_truck_fuel_logs(session):
    # show trucks so user can pick an ID
    list_trucks(session) 
    try:
        id_ = int(input("Truck id: ").strip())  # to ask user for truck ID to view its fuel logs
    except ValueError:
        print("Invalid id (must be a number).")
        return

    truck = Truck.find_by_id(session, id_) #uses helper from CRUDMixin in models.py
    if not truck:
        print("Truck not found.")
        return

    logs = truck.fuel_logs  # uses the relationship
    if not logs:
        print(f"No fuel logs for truck {truck.plate}.") # incsase there are no logs
        return

    print(f"\nFuel logs for {truck.plate}:") # display the fuel logs in a readable format
    for fl in logs:
        total = fl.liters * fl.price_per_liter # calculating the total cost of fuel log
        print(
            f"[{fl.id}] {fl.date} | {fl.vendor} @ {fl.location} | "
            f"{fl.liters} L @ {fl.price_per_liter}/L | ODO {fl.odometer} | cost {total:.2f}"
        )


# ---- MENU ----
def trucks_menu(session):
    while True:
        print("\n-- Trucks --") #using \n to create a new line for better readability and looping the menu until user decides to go back
        print("1) List all")
        print("2) Create")
        print("3) Delete")
        print("4) Find by plate") 
        print("5) View related fuel logs") 
        print("0) Back")
        choice = input("Choose: ").strip()
        if choice == "1":
            list_trucks(session)
        elif choice == "2":
            create_truck(session)
        elif choice == "3":
            delete_truck(session)
        elif choice == "4":          
            find_truck_by_plate(session)
        elif choice == "5":                   
            view_truck_fuel_logs(session)
        elif choice == "0":
            break
        else:
            print("Invalid option.")

def main_menu():
    session = SessionLocal()
    try:
        while True:
            print("\n=== Fuel Logistics CLI ===")
            print("1) Trucks")
            print("0) Exit")
            choice = input("Choose: ").strip()
            if choice == "1":
                trucks_menu(session)
            elif choice == "0":
                print("Goodbye!")
                break
            else:
                print("Invalid option.")
    finally:
        session.close()



# ---------- Fuel Logs: LIST + CREATE ----------

def list_fuel_logs(session): #list all fuel logs
    logs = FuelLog.get_all(session) #helper from CRUDMixin in models.py
    if not logs:
      print("No fuel logs.")
      return
    for fl in logs:
        total = fl.liters * fl.price_per_liter # calculating total cost of each fuel log
        print(
            f"[{fl.id}] Truck {fl.truck_id} | {fl.date} | " # displays fuel log info in a readable format
            f"{fl.liters} L @ {fl.price_per_liter}/L | "
            f"{fl.vendor} ({fl.location}) | ODO {fl.odometer} | cost {total:.2f}"
        )

def create_fuel_log(session):
    # pick a truck first
    list_trucks(session)
    try:
        truck_id = int(input("Truck id: ").strip())
    except ValueError:
        print("Invalid id.")
        return

    truck = Truck.find_by_id(session, truck_id)
    if not truck:
        print("Truck not found.")
        return

    # collect details
    try:
        liters = float(input("Liters: ").strip())
        price = float(input("Price per liter: ").strip())
    except ValueError:
        print("Liters and price must be numbers.")
        return

    vendor = input("Vendor: ").strip()
    location = input("Location: ").strip()
    if not vendor or not location:
        print("Vendor and location cannot be empty.")
        return

    try:
        odometer = float(input("Odometer: ").strip() or "0")
    except ValueError:
        print("Odometer must be a number (or blank).")
        return

    note = input("Note (optional): ").strip() or None

    # create the fuel log
    try:
        log = FuelLog.create(
            session,
            truck_id=truck.id,
            date=date.today(),
            liters=liters,
            price_per_liter=price,
            vendor=vendor,
            location=location,
            odometer=odometer,
            note=note
        )
        print(f"Fuel log #{log.id} created for {truck.plate}.")
    except Exception as e:
        session.rollback()
        print("Error:", e)

def delete_fuel_log(session):
    # show logs so user can see IDs
    list_fuel_logs(session)
    try:
        id_ = int(input("Fuel log id to delete: ").strip())
    except ValueError:
        print("Invalid id (must be a number).")
        return

    ok = FuelLog.delete(session, id_)
    print("Deleted." if ok else "Fuel log not found.")

# *--- FIND FUEL LOGS BY VENDOR ----
def find_fuel_logs_by_vendor(session):
    vendor = input("Vendor to search: ").strip()
    if not vendor:
        print("Vendor cannot be empty.")
        return
    # case-insensitive match
    logs = (session.query(FuelLog)
            .filter(FuelLog.vendor.ilike(vendor))  # exact case-insensitive
            .all())
    if not logs:
        # try partial match if exact didn’t find anything
        logs = (session.query(FuelLog)
                .filter(FuelLog.vendor.ilike(f"%{vendor}%"))
                .all())
    if not logs:
        print("No logs found for that vendor.")
        return

    for fl in logs:
        total = fl.liters * fl.price_per_liter
        print(
            f"[{fl.id}] Truck {fl.truck_id} | {fl.date} | "
            f"{fl.liters} L @ {fl.price_per_liter}/L | "
            f"{fl.vendor} ({fl.location}) | ODO {fl.odometer} | cost {total:.2f}"
        )

# *--- FIND FUEL LOGS BY DATE RANGE ----
def find_fuel_logs_by_date_range(session):
    """
    Ask for start/end dates (YYYY-MM-DD) and list matching fuel logs (inclusive).
    """
    start_s = input("Start date (YYYY-MM-DD): ").strip()
    end_s   = input("End date   (YYYY-MM-DD): ").strip()

    # parse & validate
    try:
        start = datetime.strptime(start_s, "%Y-%m-%d").date()
        end   = datetime.strptime(end_s,   "%Y-%m-%d").date()
    except ValueError:
        print("Dates must be in format YYYY-MM-DD (e.g., 2025-08-27).")
        return

    if end < start:
        print("End date can’t be before start date.")
        return

    # query (inclusive range)
    logs = (session.query(FuelLog)
            .filter(FuelLog.date.between(start, end))
            .order_by(FuelLog.date.asc())
            .all())

    if not logs:
        print("No fuel logs in that date range.")
        return

    print(f"\nFuel logs from {start} to {end}:")
    for fl in logs:
        total = fl.liters * fl.price_per_liter
        print(
            f"[{fl.id}] {fl.date} | Truck {fl.truck_id} | "
            f"{fl.liters} L @ {fl.price_per_liter}/L | "
            f"{fl.vendor} ({fl.location}) | ODO {fl.odometer} | cost {total:.2f}"
        )




def fuel_logs_menu(session):
    while True:
        print("\n-- Fuel Logs --")
        print("1) List all")
        print("2) Create")
        print("3) Delete") 
        print("4) Find by vendor")
        print("5) Find by date range") 
        print("0) Back")
        c = input("Choose: ").strip()
        if c == "1":
            list_fuel_logs(session)
        elif c == "2":
            create_fuel_log(session)
        elif c == "3":         
            delete_fuel_log(session)
        elif c == "4":               
            find_fuel_logs_by_vendor(session)
        elif c == "5":                    
            find_fuel_logs_by_date_range(session)
        elif c == "0":
            break
        else:
            print("Invalid option.")

# ---------- MAIN MENU ----------
def main_menu():
    session = SessionLocal()
    try:
        while True:
            print("\n=== Fuel Logistics CLI ===")
            print("1) Trucks")
            print("2) Fuel Logs")     
            print("0) Exit")
            choice = input("Choose: ").strip()
            if choice == "1":
                trucks_menu(session)
            elif choice == "2":        
                fuel_logs_menu(session)
            elif choice == "0":
                print("Goodbye!")
                break
            else:
                print("Invalid option.")
    finally:
        session.close()

#
# ---------------- Drivers ----------------

def list_drivers(session):
    drivers = session.query(Driver).all() # gets all drivers from database
    if not drivers:
        print("No drivers found.")
        return
    for d in drivers:
        truck_info = f"Truck {d.assigned_truck.plate}" if getattr(d, "assigned_truck", None) else "Unassigned" # checks if driver is assigned to a truck and displays accordingly
        print(f"[{d.id}] {d.name} | Lic: {d.license_number} | {truck_info} | Status: {d.status} | Phone: {d.phone or '-'}") # display driver info in a readable format

def create_driver(session):
    name = input("Driver name: ").strip()
    lic  = input("License number: ").strip().upper()
    phone = input("Phone (optional): ").strip() or None
    status = (input("Status (active/suspended/inactive) [active]: ").strip() or "active").lower()
    try:
        d = Driver.create(session, name=name, license_number=lic, phone=phone, status=status) # uses helper from CRUDMixin in models.py
        print(f"Created driver {d.name} (id={d.id})")
    except Exception as e:
        session.rollback() #undo any changes if error occurs
        print("Error:", e)

def delete_driver(session): #delete a driver by ID
    # show current drivers first
    list_drivers(session)
    try:
        id_ = int(input("Enter driver id to delete: ").strip()) #ask user for driver ID to delete and remove extra spaces
    except ValueError:
        print("Invalid id (must be a number).")
        return
    ok = Driver.delete(session, id_)
    print("Deleted." if ok else "Driver not found.")

def find_driver_by_license(session): #find a driver by license number
    lic = input("License to search: ").strip().upper()
    if not lic:
        print("License cannot be empty.") #this is for ensuring a driver license is provided
        return
    d = session.query(Driver).filter(Driver.license_number == lic).first() 
    if d:
        truck_info = f"Truck {d.assigned_truck.plate}" if getattr(d, "assigned_truck", None) else "Unassigned" # checks if driver is assigned to a truck and displays accordingly
        print(f"Found: [{d.id}] {d.name} | Lic: {d.license_number} | {truck_info} | Status: {d.status}") # display driver info in a readable format
    else:
        print("No match.")

def assign_driver_to_truck(session):
    # pick driver
    list_drivers(session)
    try:
        did = int(input("Driver id to assign: ").strip()) 
    except ValueError:
        print("Invalid driver id.")
        return
    d = Driver.find_by_id(session, did)
    if not d:
        print("Driver not found.")
        return

    # pick truck
    list_trucks(session)
    try:
        tid = int(input("Assign to truck id: ").strip()) # ask user for truck ID to assign the driver to
    except ValueError:
        print("Invalid truck id.")
        return
    t = Truck.find_by_id(session, tid)
    if not t:
        print("Truck not found.")
        return

    # assign
    try:
        d.assigned_truck = t
        session.commit()
        print(f"Driver {d.name} assigned to {t.plate}.")
    except Exception as e:
        session.rollback()
        print("Error:", e)

def unassign_driver(session):
    list_drivers(session)
    try:
        did = int(input("Driver id to unassign: ").strip())
    except ValueError:
        print("Invalid driver id.")
        return
    d = Driver.find_by_id(session, did)
    if not d:
        print("Driver not found.")
        return
    try:
        d.assigned_truck = None
        session.commit()
        print(f"Driver {d.name} is now unassigned.")
    except Exception as e:
        session.rollback()
        print("Error:", e)

def view_truck_drivers(session): # view all drivers assigned to a specific truck
    # pick truck
    list_trucks(session)
    try:
        tid = int(input("Truck id: ").strip())
    except ValueError:
        print("Invalid truck id.")
        return
    t = Truck.find_by_id(session, tid)
    if not t:
        print("Truck not found.")
        return
    if not getattr(t, "drivers", []):
        print(f"No drivers assigned to {t.plate}.")
        return
    print(f"\nDrivers for {t.plate}:")
    for d in t.drivers:
        print(f"[{d.id}] {d.name} | Lic: {d.license_number} | Status: {d.status} | Phone: {d.phone or '-'}")
# ---- Drivers Menu ----
def drivers_menu(session):
    while True:
        print("\n-- Drivers --")
        print("1) List all")
        print("2) Create")
        print("3) Delete")
        print("4) Find by license")
        print("5) Assign to truck")
        print("6) Unassign from truck")
        print("7) View drivers for a truck")
        print("0) Back")
        c = input("Choose: ").strip()
        if c == "1":
            list_drivers(session)
        elif c == "2":
            create_driver(session)
        elif c == "3":
            delete_driver(session)
        elif c == "4":
            find_driver_by_license(session)
        elif c == "5":
            assign_driver_to_truck(session)
        elif c == "6":
            unassign_driver(session)
        elif c == "7":
            view_truck_drivers(session)
        elif c == "0":
            break
        else:
            print("Invalid option.")

#Main menu updated to include Drivers
def main_menu():
    session = SessionLocal()
    try:
        while True:
            print("\n=== Fuel Logistics CLI ===")
            print("1) Trucks")
            print("2) Fuel Logs")
            print("3) Drivers")     # ← add
            print("0) Exit")
            choice = input("Choose: ").strip()
            if choice == "1":
                trucks_menu(session)
            elif choice == "2":
                fuel_logs_menu(session)
            elif choice == "3":      # ← add
                drivers_menu(session)
            elif choice == "0":
                print("Goodbye!")
                break
            else:
                print("Invalid option.")
    finally:
        session.close()
