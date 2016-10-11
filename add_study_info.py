"""Add extra study information into the database.
"""

from app import db
from app.models import Study, Person

andt = Study.query.filter(Study.nickname == 'ANDT').first()
andt.description = 'Comparison of Underweight vs. Weight-Recovered Subjects ' \
                   'and Healthy Controls'
andt.fullname = 'A Pilot Study of Diffusion Tensor Imaging in Anorexia ' \
                'Nervosa: Comparison of Underweight vs. Weight-Recovered ' \
                'Subjects and Healthy Controls'

contact = Person()
contact.name = "Amy Miles"
contact.email = "amy.miles@camh.ca"

andt.primary_contact = contact

db.session.commit()
