import streamlit as st
import json
from datetime import datetime, timedelta
import smtplib
import random
from email.mime.text import MIMEText  
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
import csv

# Constants
DATA_FILE = 'birthdays.csv'
MESSAGES_FILE = 'messages.json'

# Models
class Person:
    def __init__(self, name: str, email: str, birthday: str, message_id: int = None):
        self.name = name
        self.email = email
        self.birthday = datetime.strptime(birthday, '%Y-%m-%d').date()
        self.message_id = message_id

    def to_dict(self):
        return {
            'name': self.name,
            'email': self.email,
            'birthday': self.birthday.strftime('%Y-%m-%d'),
            'message_id': self.message_id
        }

    @staticmethod
    def from_dict(data):
        return Person(
            name=data['name'],
            email=data['email'],
            birthday=data['birthday'],
            message_id=data.get('message_id')
        )

class MessageManager:
    def __init__(self):
        self.messages = self.load_messages()

    def load_messages(self) -> List[str]:
        try:
            with open(MESSAGES_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_messages(self):
        with open(MESSAGES_FILE, 'w') as f:
            json.dump(self.messages, f)

    def add_message(self, message: str):
        self.messages.append(message)
        self.save_messages()

    def get_message(self, index: int = None) -> str:
        if index is not None and 0 <= index < len(self.messages):
            return self.messages[index]
        return random.choice(self.messages) if self.messages else "Feliz cumpleaños!"

class BirthdayManager:
    def __init__(self, filename=DATA_FILE):
        self.filename = filename
        self.people: List[Person] = self.load_birthdays()

    def load_birthdays(self) -> List[Person]:
        people = []
        try:
            with open(self.filename, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    people.append(Person(
                        name=row['name'],
                        email=row['email'],
                        birthday=row['birthday'],
                        message_id=int(row['message_id']) if row['message_id'] else None
                    ))
        except FileNotFoundError:
            pass
        return people

    def save_birthdays(self):
        with open(self.filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'email', 'birthday', 'message_id'])  # header
            for person in self.people:
                writer.writerow([
                    person.name, 
                    person.email, 
                    person.birthday.strftime('%Y-%m-%d'), 
                    person.message_id if person.message_id is not None else ''
                ])

    def add_person(self, person: Person):
        self.people.append(person)
        self.save_birthdays()

    def get_upcoming_birthdays(self) -> List[Dict]:
        today = datetime.now().date()
        upcoming = []
        for person in self.people:
            bday = person.birthday.replace(year=today.year)
            if bday < today:
                bday = bday.replace(year=today.year + 1)
            days_remaining = (bday - today).days
            upcoming.append({
                'name': person.name,
                'email': person.email,
                'days_remaining': days_remaining,
                'birthday': bday,
                'message_id': person.message_id
            })
        return sorted(upcoming, key=lambda x: x['days_remaining'])

# Email sender (configure your SMTP credentials)
def send_email(to_email: str, subject: str, body: str):
    from_email = 'youremail@example.com'
    password = 'yourpassword'
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP('smtp.example.com', 587) as server:
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)

# Streamlit UI
st.title("Gestor de Cumpleaños 🎉")
bd_manager = BirthdayManager()
msg_manager = MessageManager()

st.header("🎂 Próximos Cumpleaños")
upcoming = bd_manager.get_upcoming_birthdays()
for person in upcoming:
    st.write(f"{person['name']} ({person['email']}) - Cumpleaños en {person['days_remaining']} días")

st.header("➕ Registrar nuevo cumpleaños")
name = st.text_input("Nombre")
email = st.text_input("Correo electrónico")
birthday = st.date_input("Fecha de cumpleaños")
message_option = st.selectbox("Mensaje personalizado", ["Aleatorio"] + [f"Mensaje {i+1}" for i in range(len(msg_manager.messages))])

if st.button("Guardar cumpleaños"):
    message_id = None if message_option == "Aleatorio" else int(message_option.split()[1]) - 1
    bd_manager.add_person(Person(name, email, birthday.strftime('%Y-%m-%d'), message_id))
    st.success("Cumpleaños registrado correctamente!")

st.header("✏️ Administrar mensajes de felicitación")
new_message = st.text_area("Nuevo mensaje de felicitación")
if st.button("Agregar mensaje"):
    msg_manager.add_message(new_message)
    st.success("Mensaje agregado correctamente")

st.subheader("Mensajes guardados:")
for idx, msg in enumerate(msg_manager.messages):
    st.markdown(f"**Mensaje {idx+1}:** {msg}")

# Auto email sender simulation
st.header("✉️ Simulación de envío de felicitaciones")
today = datetime.now().date()
for person in bd_manager.people:
    if person.birthday.month == today.month and person.birthday.day == today.day:
        message = msg_manager.get_message(person.message_id)
        send_email(person.email, "¡Feliz cumpleaños!", message)
        st.info(f"Correo enviado a {person.name} ({person.email})")
