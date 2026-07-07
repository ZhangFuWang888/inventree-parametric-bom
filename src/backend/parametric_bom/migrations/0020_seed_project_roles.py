"""Seed default roles for all existing projects and migrate old membership data.

- Creates "管理员" and "成员" preset roles per project
- Migrates project.members (M2M) → ProjectMembership with "成员" role
- Migrates project.manager (FK) → ProjectMembership with "管理员" role
- Creates membership for owner with "管理员" role
"""
from django.db import migrations

PRESET_ADMIN_PERMS = [
    'view_project', 'edit_project', 'manage_members',
    'manage_items', 'generate_orders', 'view_cost',
    'export_report', 'manage_attachments', 'view_logs',
]

PRESET_MEMBER_PERMS = [
    'view_project', 'view_cost', 'export_report', 'view_logs',
]


def seed_roles(apps, schema_editor):
    Project = apps.get_model('parametric_bom', 'Project')
    ProjectRole = apps.get_model('parametric_bom', 'ProjectRole')
    ProjectMembership = apps.get_model('parametric_bom', 'ProjectMembership')

    for project in Project.objects.all():
        # Create admin role
        admin_role, _ = ProjectRole.objects.get_or_create(
            project=project,
            name='管理员',
            defaults={
                'permissions': PRESET_ADMIN_PERMS,
                'is_preset': True,
            },
        )
        # Create member role
        member_role, _ = ProjectRole.objects.get_or_create(
            project=project,
            name='成员',
            defaults={
                'permissions': PRESET_MEMBER_PERMS,
                'is_preset': True,
            },
        )

        # Assign owner as admin
        if project.owner:
            ProjectMembership.objects.get_or_create(
                project=project,
                user=project.owner,
                defaults={'role': admin_role},
            )

        # Migrate existing manager → admin role
        if project.manager and project.manager != project.owner:
            ProjectMembership.objects.get_or_create(
                project=project,
                user=project.manager,
                defaults={'role': admin_role},
            )

        # Migrate existing members → member role
        for user in project.members.all():
            if user == project.owner or user == project.manager:
                continue
            ProjectMembership.objects.get_or_create(
                project=project,
                user=user,
                defaults={'role': member_role},
            )


class Migration(migrations.Migration):

    dependencies = [
        ('parametric_bom', '0019_projectrole_projectmembership'),
    ]

    operations = [
        migrations.RunPython(seed_roles, reverse_code=migrations.RunPython.noop),
    ]
