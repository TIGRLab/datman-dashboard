"""Timepoint blueprint email notifications.
"""

from ...emails import send_email


def incidental_finding_email(user, timepoint, comment):
    """Notify admins about an incidental finding reported during QC.

    Args:
        user (:obj:`str`): The reporting user's name
        timepoint (:obj:`str`): The timepoint with an incidental finding.
        comment (:obj:`str`): The descriptive comment entered by the user.
    """
    subject = 'IMPORTANT: Incidental Finding flagged'
    body = '{} has reported an incidental finding for {}. ' \
           'Description: {}'.format(user, timepoint, comment)
    send_email(subject, body)
