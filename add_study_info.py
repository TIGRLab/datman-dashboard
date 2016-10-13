"""Add extra study information into the database."""

from app import db
from app.models import Study, Person, get_if_exists

new_info = {study}


andt = get_if_exists(Study(nickname='ANDT'))

andt.description = 'Comparison of Underweight vs. Weight-Recovered Subjects ' \
                   'and Healthy Controls'
andt.fullname = 'A Pilot Study of Diffusion Tensor Imaging in Anorexia ' \
                'Nervosa: Comparison of Underweight vs. Weight-Recovered ' \
                'Subjects and Healthy Controls'

andt_contact = get_if_exists(Person(email="amy.miles@camh.ca"))
andt_contact.name = "Amy Miles"

andt.primary_contact = andt.contact
##############
asdd = get_if_exists(Study(nickname='ASDD'))

asdd.fullname = 'Autism Spectrum Disorder Study'

asdd_contact = get_if_exists(Person(email="stephanie.ameis@camh.ca"))
asdd_contact.name = "Stephanie Ameis"

asdd.primary_contact = asdd_contact
###############
cogbdo = get_if_exists(Study(nickname='COGBDO'))

cogbdo.description =
