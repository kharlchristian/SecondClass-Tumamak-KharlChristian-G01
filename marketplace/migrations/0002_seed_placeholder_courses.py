from django.db import migrations


COURSES = (
    ("CSIT321", "Applications Development and Emerging Technologies"),
    ("CSIT340", "Industry Elective 1"),
    ("IT365", "Data Analytics 1"),
    ("CSIT212", "Quantitative Methods"),
    ("CSIT284", "Platform-based Development 3 (Mobile)"),
    ("CSIT227", "Object-oriented Programming1"),
    ("CSIT228", "Object-oriented Programming 2"),
    ("CSIT111", "Introduction to Computing"),
)


def seed_placeholder_courses(apps, schema_editor):
    Course = apps.get_model("marketplace", "Course")
    database = schema_editor.connection.alias
    for course_code, course_name in COURSES:
        Course.objects.using(database).get_or_create(
            course_code=course_code,
            defaults={"course_name": course_name},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_placeholder_courses, migrations.RunPython.noop),
    ]
