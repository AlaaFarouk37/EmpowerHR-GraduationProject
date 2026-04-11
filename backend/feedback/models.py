import uuid
from django.db import models
from django.conf import settings



def gen_id():
    return uuid.uuid4().hex[:20]



class FeedbackForm(models.Model):
    """
    A feedback form created by an admin.
    Contains a set of questions employees will answer.
    """
    formID           = models.CharField(max_length=50, primary_key=True, default=gen_id)
    title            = models.CharField(max_length=200)
    description      = models.TextField(blank=True, null=True)
    createdByAdminID = models.ForeignKey(
                         settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                         null=True, blank=True,
                         db_column='createdByAdminID',
                         related_name='created_forms')
    createdAt        = models.DateTimeField(auto_now_add=True)
    isActive         = models.BooleanField(default=True)

    class Meta:
        db_table = 'FeedbackForm'
        ordering = ['-createdAt']

    def save(self, *args, **kwargs):
        if self.isActive:
            # Deactivate all other forms when this one is set to active
            FeedbackForm.objects.exclude(pk=self.formID).update(isActive=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class FeedbackQuestion(models.Model):
    """
    A single question belonging to a FeedbackForm.
    fieldType determines which answer column is used in FeedbackAnswer.
    """
    FIELD_TYPES = [
        ('score_1_4', 'Score 1-4'),
        ('boolean',   'Yes / No'),
        ('decimal',   'Decimal Number'),
    ]

    questionID   = models.CharField(max_length=50, primary_key=True, default=gen_id)
    formID       = models.ForeignKey(
                     FeedbackForm, on_delete=models.CASCADE,
                     db_column='formID',
                     related_name='questions')
    questionText = models.CharField(max_length=300)
    fieldType    = models.CharField(max_length=20, choices=FIELD_TYPES)
    order        = models.IntegerField(default=0)

    class Meta:
        db_table = 'FeedbackQuestion'
        ordering = ['order']

    def __str__(self):
        return f"[{self.fieldType}] {self.questionText[:60]}"


class FeedbackSubmission(models.Model):
    """
    One submission per employee per form.
    Created when the form is assigned; status flips to Completed on submit.
    """
    STATUS_PENDING   = 'Pending'
    STATUS_COMPLETED = 'Completed'
    STATUS_CHOICES   = [
        (STATUS_PENDING,   'Pending'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    submissionID = models.CharField(max_length=50, primary_key=True, default=gen_id)
    formID       = models.ForeignKey(
                     FeedbackForm, on_delete=models.CASCADE,
                     db_column='formID',
                     related_name='submissions')
    employeeID = models.ForeignKey(
                    settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                    db_column='employeeID',
                    to_field='employee_id',
                    related_name='submissions')
    
    submittedAt  = models.DateTimeField(null=True, blank=True)
    status       = models.CharField(
                     max_length=20, choices=STATUS_CHOICES,
                     default=STATUS_PENDING)

    class Meta:
        db_table      = 'FeedbackSubmission'
        unique_together = ('formID', 'employeeID')

    def __str__(self):
        return f"Submission {self.submissionID} — {self.employeeID_id} — {self.status}"


class FeedbackAnswer(models.Model):
    """
    One answer row per question per submission.
    Only one of scoreValue / booleanValue / decimalValue
    will be populated depending on the question's fieldType.
    """
    answerID     = models.CharField(max_length=50, primary_key=True, default=gen_id)
    submissionID = models.ForeignKey(
                     FeedbackSubmission, on_delete=models.CASCADE,
                     db_column='submissionID',
                     related_name='answers')
    questionID   = models.ForeignKey(
                     FeedbackQuestion, on_delete=models.CASCADE,
                     db_column='questionID',
                     related_name='answers')
    scoreValue   = models.IntegerField(null=True, blank=True)
    booleanValue = models.BooleanField(null=True, blank=True)
    decimalValue = models.DecimalField(
                     max_digits=8, decimal_places=2,
                     null=True, blank=True)

    class Meta:
        db_table      = 'FeedbackAnswer'
        unique_together = ('submissionID', 'questionID')

    def __str__(self):
        return f"Answer {self.answerID} — Q:{self.questionID_id}"