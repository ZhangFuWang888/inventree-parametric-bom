"""Management command: sync projects from external ERP API.

Usage:
    python manage.py sync_projects_from_erp

Scheduled via cron (recommended: daily):
    0 6 * * * cd /path/to/InvenTree && venv/bin/python manage.py sync_projects_from_erp
"""

import json
import logging
from urllib.request import urlopen, Request

from django.core.management.base import BaseCommand
from django.utils import timezone

from parametric_bom.models import Project

logger = logging.getLogger('inventree')

ERP_API_URL = 'https://erp.blueswords.com/jn/api/work/tdWorkProject/getProjectListInDD'

# Default user ID for synced projects (admin)
DEFAULT_OWNER_ID = 1


class Command(BaseCommand):
    """Sync projects from external ERP system."""

    help = 'Sync project list from external ERP API (daily)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-url',
            default=ERP_API_URL,
            help='ERP API URL (default: %s)' % ERP_API_URL,
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be done without making changes',
        )

    def handle(self, *args, **options):
        api_url = options['api_url']
        dry_run = options['dry_run']

        self.stdout.write(f'Syncing projects from ERP: {api_url}')
        logger.info(f'Syncing projects from ERP: {api_url}')

        try:
            req = Request(api_url, method='GET')
            with urlopen(req, timeout=30) as resp:
                raw = resp.read().decode('utf-8')
                data = json.loads(raw)
        except Exception as e:
            self.stderr.write(f'ERROR: Failed to fetch ERP API: {e}')
            logger.error(f'ERP sync failed to fetch: {e}')
            return

        if not data.get('success') or data.get('code') != 200:
            self.stderr.write(f'ERROR: ERP API returned error: {data.get("msg")}')
            return

        items = data.get('list', [])
        self.stdout.write(f'Fetched {len(items)} projects from ERP')

        if dry_run:
            self.stdout.write('DRY RUN — no changes made')
            for item in items[:5]:
                self.stdout.write(f'  Would create/update: {item.get("projectCode")} — {item.get("projectName")}')
            return

        # Track which external IDs we see
        seen_ids = set()
        created = 0
        updated = 0

        for item in items:
            ext_id = str(item.get('id', '')).strip()
            name = (item.get('projectName') or '').strip()
            code = (item.get('projectCode') or '').strip()
            address = (item.get('receivingAddress') or '').strip()

            if not ext_id or not name:
                continue

            seen_ids.add(ext_id)

            # Upsert by external_id
            project, was_created = Project.objects.update_or_create(
                external_id=ext_id,
                defaults={
                    'name': name,
                    'project_code': code or '',
                    'description': address or '',
                    'status': 'active',
                    'is_active': True,
                    'is_public': True,
                    'owner_id': DEFAULT_OWNER_ID,
                },
            )

            if was_created:
                created += 1
            else:
                updated += 1

        # Optionally: mark projects that no longer exist in ERP as inactive
        # (commented out for safety — user may want to keep local projects)
        # Project.objects.filter(
        #     external_id__in=seen_ids, external_id__gt=''
        # ).exclude(external_id__in=seen_ids).update(is_active=False)

        self.stdout.write(self.style.SUCCESS(
            f'Sync complete: {created} created, {updated} updated'
        ))
        logger.info(
            f'ERP project sync complete: {created} created, {updated} updated'
        )
