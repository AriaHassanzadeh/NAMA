import django.db.models.deletion
import django.db.models.functions.text
from django.conf import settings
from django.db import migrations, models


def check_duplicate_emails(apps, schema_editor):
    user = apps.get_model("accounts", "User")
    duplicate = (
        user.objects.using(schema_editor.connection.alias).exclude(email="")
        .annotate(normalized_email=django.db.models.functions.text.Lower(django.db.models.functions.text.Trim("email")))
        .values("normalized_email").annotate(total=models.Count("pk"))
        .filter(total__gt=1).exists()
    )
    if duplicate:
        raise RuntimeError(
            "Cannot add unique email constraint: duplicate nonblank email addresses exist. "
            "Resolve them explicitly before migrating; no accounts were changed."
        )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(check_duplicate_emails, migrations.RunPython.noop),
        migrations.CreateModel(
            name='EmailVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('token_hash', models.CharField(max_length=64, unique=True)),
                ('sent_at', models.DateTimeField()),
                ('expires_at', models.DateTimeField()),
                ('consumed_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='email_verification_required',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='email_verified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.UniqueConstraint(django.db.models.functions.text.Lower(django.db.models.functions.text.Trim('email')), condition=models.Q(('email', ''), _negated=True), name='accounts_user_email_ci_unique'),
        ),
        migrations.AddField(
            model_name='emailverification',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='email_verification', to=settings.AUTH_USER_MODEL),
        ),
    ]
