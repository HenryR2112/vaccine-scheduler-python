from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime
import time


'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None


def create_patient(tokens):
    # create_patient <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_patient(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    patient = Patient(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        patient.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)
    display_command()


def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Patients WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    caregiver = Caregiver(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        caregiver.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)
    display_command()


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def login_patient(tokens):
    # login_patient <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_patient
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if patient is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_patient = patient
    display_command()


def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if caregiver is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_caregiver = caregiver
    display_command()


def search_caregiver_schedule(tokens):
    global current_caregiver
    global current_patient
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return

    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    # Output the username for the caregivers that are available for the date, along 
    # with the number of available doses left for each vaccine.
    # Order by the username of the caregiver. Separate each attribute with a space.
    query_caregiver = 'SELECT Username FROM Availabilities WHERE Time = %s ORDER BY Username'
    get_all_vaccines = "SELECT Name, Doses FROM vaccines"
    try:
        d = datetime.datetime(year, month, day)
        cursor.execute(query_caregiver, (d,))  # pass parameters as a tuple
        for row in cursor.fetchall():
            print("Available Caregiver: " + str(row[0]))  # Access tuple using integer index
            print('-------------------------------')
        cursor.execute(get_all_vaccines)
        print("***********************************")
        for row in cursor.fetchall():
            print("name: " + str(row[0]) + ", available_doses: " + str(row[1]))  # Access tuple using integer index
            print('-------------------------------')
    except pymssql.Error as e:
        print("Search Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when Searching")
        print("Error:", e)
        return
    print("Search Complete!")
    display_command()


def reserve(tokens):
    global current_caregiver
    global current_patient

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()
    if current_caregiver is not None:
        print("Please login as a patient!")
        return

    if current_patient is None:
        print("Please login as a patient first!")
        return

    if len(tokens) != 3:
        print("Please try again!")
        return

    date = tokens[1]
    vaccine = tokens[2]

    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])

    try:
        d = datetime.datetime(year, month, day)

        # Check if there is an available caregiver for the specified date
        query_caregiver = 'SELECT TOP 1 Username FROM Availabilities WHERE Time = %s'
        cursor.execute(query_caregiver, (d,))
        available_caregivers = cursor.fetchall()

        if len(available_caregivers) > 0:
            caregiver_username = available_caregivers[0][0]
            # Check if there are enough vaccine doses available
            get_vaccine_doses = "SELECT Doses FROM Vaccines WHERE Name = %s"
            cursor.execute(get_vaccine_doses, (vaccine,))
            available_doses = cursor.fetchone()[0]
            if available_doses > 0:
                # Update caregiver's availability
                update_availability = "DELETE FROM Availabilities WHERE Username = %s AND Time = %s"
                cursor.execute(update_availability, (caregiver_username, d))
                # Update vaccine doses
                update_vaccine = "UPDATE Vaccines SET Doses = Doses - 1 WHERE Name = %s"
                cursor.execute(update_vaccine, (vaccine,))
                # Generate and print appointment ID
                get_appointment_id = 'SELECT max(appointment_id) FROM Appointments'
                cursor.execute(get_appointment_id)
                appointment_id = cursor.fetchall()[0][0]
                if appointment_id is None:
                    appointment_id = 1
                else:
                    appointment_id += 1
                    print(appointment_id)
                insert_appointment = "INSERT INTO Appointments (appointment_id, vaccine_name, Time, CUsername, PUsername) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(insert_appointment, (appointment_id, vaccine, d, caregiver_username, current_patient.get_username()))
                print(f"Appointment ID: {appointment_id}, Caregiver username: {caregiver_username}")
            else:
                print("Not enough available doses!")
        else:
            print("No Caregiver is available!")

    except pymssql.Error as e:
        print("Search Failed")
        print("Db-Error:", e)
    except Exception as e:
        print("Error occurred when Reserving")
        print("Error:", e)
    else:
        conn.commit()
        print("Reservation Complete!")

    display_command()


def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        current_caregiver.upload_availability(d)
    except pymssql.Error as e:
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when uploading availability")
        print("Error:", e)
        return
    print("Availability uploaded!")
    display_command()


def cancel(tokens):
    global current_caregiver
    global current_patient

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return

    if len(tokens) != 2:
        print("Please try again!")
        return
    
    appointment_id = tokens[1]
    try:
        if current_caregiver is not None:
            # Cancel appointment for caregiver
            query_appointment = '''
                SELECT appointment_id, Time, PUsername, vaccine_name
                FROM Appointments
                WHERE CUsername = %s
                AND appointment_id = %s
            '''
            cursor.execute(query_appointment, (current_caregiver.get_username(), appointment_id))
            caregiver_appointment = cursor.fetchone()

            if caregiver_appointment:
                appointment_id, appointment_time, patient_username, vaccine = caregiver_appointment

                # Update vaccine count
                print(vaccine)
                update_vaccine = "UPDATE Vaccines SET Doses = Doses + 1 WHERE Name = %s"
                cursor.execute(update_vaccine, (vaccine,))
                # Roll back availability
                return_availability = "INSERT INTO Availabilities (Username, Time) VALUES (%s, %s)"
                cursor.execute(return_availability, (current_caregiver.get_username(), appointment_time))

                # Delete appointment
                delete_appointment = "DELETE FROM Appointments WHERE appointment_id = %s"
                cursor.execute(delete_appointment, (appointment_id,))

                print(f"Appointment {appointment_id} canceled successfully.")
            else:
                print("Appointment not found for this caregiver.")

        elif current_patient is not None:
            # Cancel appointment for patient
            query_appointment = '''
                SELECT appointment_id, Time, CUsername, vaccine_name
                FROM Appointments
                WHERE PUsername = %s
                AND appointment_id = %s
            '''
            cursor.execute(query_appointment, (current_patient.get_username(), appointment_id))
            patient_appointment = cursor.fetchone()

            if patient_appointment:
                appointment_id, appointment_time, caregiver_username, vaccine = patient_appointment


                update_vaccine = "UPDATE Vaccines SET Doses = Doses + 1 WHERE Name = %s"
                cursor.execute(update_vaccine, (vaccine,))

                # Roll back availability for the caregiver
                return_availability = "INSERT INTO Availabilities (Username, Time) VALUES (%s, %s)"
                cursor.execute(return_availability, (caregiver_username, appointment_time))

                # Delete appointment
                delete_appointment = "DELETE FROM Appointments WHERE appointment_id = %s"
                cursor.execute(delete_appointment, (appointment_id,))

                print(f"Appointment {appointment_id} canceled successfully.")
            else:
                print("Appointment not found for this patient.")

    except pymssql.Error as e:
        print("Please try again!")
        print("Db-Error:", e)
    except Exception as e:
        print("Please try again!")
        print("Error:", e)
    finally:
        conn.commit()
        conn.close()
    display_command()


def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None
    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except pymssql.Error as e:
        print("Error occurred when adding doses")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when adding doses")
        print("Error:", e)
        return

    # if the vaccine is not found in the database, add a new (vaccine, doses) entry.
    # else, update the existing entry by adding the new doses
    if vaccine is None:
        vaccine = Vaccine(vaccine_name, doses)
        try:
            vaccine.save_to_db()
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    print("Doses updated!")
    display_command()


def show_appointments(tokens):
    global current_caregiver
    global current_patient

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    if len(tokens) != 1:
        print("Please try again!")
        return
    
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return

    try:
        if current_caregiver is not None:
            # Show appointments for caregivers
            query_appointments = '''
                SELECT appointment_id, vaccine_name, Time, PUsername
                FROM Appointments
                WHERE CUsername = %s
                ORDER BY appointment_id
            '''
            cursor.execute(query_appointments, (current_caregiver.get_username(),))
            caregiver_appointments = cursor.fetchall()

            if caregiver_appointments:
                for appointment in caregiver_appointments:
                    appointment_id, vaccine_name, appointment_time, patient_username = appointment
                    print(f"{appointment_id} {vaccine_name} {appointment_time} {patient_username}")
            else:
                print("No scheduled appointments for this caregiver.")

        elif current_patient is not None:
            # Show appointments for patients
            query_appointments = '''
                SELECT appointment_id, vaccine_name, Time, CUsername
                FROM Appointments
                WHERE PUsername = %s
                ORDER BY appointment_id
            '''
            cursor.execute(query_appointments, (current_patient.get_username(),))
            patient_appointments = cursor.fetchall()

            if patient_appointments:
                for appointment in patient_appointments:
                    appointment_id, vaccine_name, appointment_time, caregiver_username = appointment
                    print(f"{appointment_id} {vaccine_name} {appointment_time} {caregiver_username}")
            else:
                print("No scheduled appointments for this patient.")

    except pymssql.Error as e:
        print("Please try again!")
        print("Db-Error:", e)
    except Exception as e:
        print("Please try again!")
        print("Error:", e)
    finally:
        conn.close()
        display_command()


def logout(tokens):
    global current_caregiver
    global current_patient

    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    
    if len(tokens) != 1:
        print('Please try again!')

    current_caregiver = None
    current_patient = None
    print('Successfully logged out!')
    display_command()


def display_command():
    time.sleep(1)
    print()
    print(" *** Please enter one of the following commands *** ")
    print("> create_patient <username> <password>")  # //TODO: implement create_patient (Part 1)
    print("> create_caregiver <username> <password>")
    print("> login_patient <username> <password>")  # // TODO: implement login_patient (Part 1)
    print("> login_caregiver <username> <password>")
    print("> search_caregiver_schedule <date>")  # // TODO: implement search_caregiver_schedule (Part 2)
    print("> reserve <date> <vaccine>")  # // TODO: implement reserve (Part 2)
    print("> upload_availability <date>")
    print("> cancel <appointment_id>")  # // TODO: implement cancel (extra credit)
    print("> add_doses <vaccine> <number>")
    print("> show_appointments")  # // TODO: implement show_appointments (Part 2)
    print("> logout")  # // TODO: implement logout (Part 2)
    print("> Quit")
    print()


def start():
    global current_caregiver
    global current_patient
    stop = False
    print()
    print(" *** Please enter one of the following commands *** ")
    print("> create_patient <username> <password>")  # //TODO: implement create_patient (Part 1)
    print("> create_caregiver <username> <password>")
    print("> login_patient <username> <password>")  # // TODO: implement login_patient (Part 1)
    print("> login_caregiver <username> <password>")
    print("> search_caregiver_schedule <date>")  # // TODO: implement search_caregiver_schedule (Part 2)
    print("> reserve <date> <vaccine>")  # // TODO: implement reserve (Part 2)
    print("> upload_availability <date>")
    print("> cancel <appointment_id>")  # // TODO: implement cancel (extra credit)
    print("> add_doses <vaccine> <number>")
    print("> show_appointments")  # // TODO: implement show_appointments (Part 2)
    print("> logout")  # // TODO: implement logout (Part 2)
    print("> Quit")
    print()
    while not stop:
        response = ""
        print("> ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Please try again!")
            break

        response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Please try again!")
            continue
        operation = tokens[0]
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == 'cancel':
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            current_patient = None
            current_caregiver = None
            print("Bye!")
            stop = True
        else:
            print("Invalid operation name!")


if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-code these values, but we will do this ]
    // for the simplicity of this assignment
    // and then construct a map of vaccineName -> vaccineObject
    '''

    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()
