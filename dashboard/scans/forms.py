from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired

class ScanChecklistForm(FlaskForm):
    comment = TextAreaField(
        'Comment:',
        id='scan-comment',
        validators=[DataRequired()],
        render_kw={
            'placeholder': 'Add description',
            'rows': 12,
            'required': True,
            'maxlength': '1028'
        })
    submit = SubmitField('Submit')


class SliceTimingForm(FlaskForm):
    timings = TextAreaField(
        'NewTimings',
        id="new_timings",
        render_kw={
            'rows': 4,
            'cols': 65,
            'required': True,
            'placeholder': "Enter comma separated slice timings"
        })
    submit = SubmitField('Update', id='submit_timings')
