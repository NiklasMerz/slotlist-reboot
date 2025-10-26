from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from api.models import User, MissionSlot, MissionSlotRegistration


class Command(BaseCommand):
    help = 'Check for duplicate user nicknames and merge imported users with real Steam users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be merged without making changes',
        )
        parser.add_argument(
            '--auto-merge',
            action='store_true',
            help='Automatically merge imported users with matching real users',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        auto_merge = options['auto_merge']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))

        # Find duplicate nicknames
        self.stdout.write('\n=== Checking for duplicate nicknames ===')
        duplicates = User.objects.values('nickname').annotate(
            count=Count('nickname')
        ).filter(count__gt=1).order_by('-count')

        if not duplicates.exists():
            self.stdout.write(self.style.SUCCESS('No duplicate nicknames found!'))
            return

        total_duplicates = duplicates.count()
        self.stdout.write(f'Found {total_duplicates} nicknames with duplicates\n')

        merge_count = 0
        skip_count = 0

        for dup in duplicates:
            nickname = dup['nickname']
            users = User.objects.filter(nickname=nickname).order_by('created_at')
            
            # Separate imported and real users
            imported_users = [u for u in users if u.steam_id.startswith('imported_')]
            real_users = [u for u in users if not u.steam_id.startswith('imported_')]

            self.stdout.write(f'\nNickname: "{nickname}" ({dup["count"]} users)')
            
            for user in users:
                is_imported = user.steam_id.startswith('imported_')
                user_type = 'IMPORTED' if is_imported else 'REAL'
                slot_count = MissionSlot.objects.filter(assignee=user).count()
                reg_count = MissionSlotRegistration.objects.filter(user=user).count()
                community_info = f'community: {user.community.slug}' if user.community else 'no community'
                
                self.stdout.write(
                    f'  [{user_type}] {user.uid} - {user.steam_id} '
                    f'(slots: {slot_count}, registrations: {reg_count}, '
                    f'{community_info}, created: {user.created_at.strftime("%Y-%m-%d")})'
                )

            # Check if we can merge
            if len(real_users) == 1 and len(imported_users) > 0:
                real_user = real_users[0]
                
                if auto_merge:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  → Merging {len(imported_users)} imported user(s) into real user {real_user.uid}'
                        )
                    )
                    
                    if not dry_run:
                        merge_count += self._merge_users(imported_users, real_user)
                    else:
                        merge_count += len(imported_users)
                else:
                    self.stdout.write(
                        self.style.NOTICE(
                            f'  → Can merge {len(imported_users)} imported user(s) into {real_user.uid} '
                            f'(use --auto-merge to perform)'
                        )
                    )
            elif len(real_users) > 1:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ⚠ Multiple real users with same nickname - manual review required'
                    )
                )
                skip_count += 1
            elif len(real_users) == 0:
                self.stdout.write(
                    self.style.NOTICE(
                        f'  → All users are imported - no merge possible'
                    )
                )
                skip_count += 1

        # Summary
        self.stdout.write('\n' + '=' * 60)
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'Would merge {merge_count} users'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Merged {merge_count} users'))
        
        if skip_count > 0:
            self.stdout.write(
                self.style.WARNING(f'Skipped {skip_count} nicknames requiring manual review')
            )

    def _merge_users(self, imported_users, target_user):
        """
        Merge imported users into a real user.
        
        Transfers all slot assignments, registrations, and community membership
        to the target user, then deletes the imported users.
        
        Args:
            imported_users: List of imported User instances to merge
            target_user: Real User instance to merge into
            
        Returns:
            Number of users merged
        """
        merged_count = 0
        
        with transaction.atomic():
            for imported_user in imported_users:
                # Transfer community if target doesn't have one but imported user does
                if imported_user.community and not target_user.community:
                    target_user.community = imported_user.community
                    target_user.save(update_fields=['community'])
                    self.stdout.write(
                        f'    Transferred community: {imported_user.community.name} ({imported_user.community.slug})'
                    )
                elif imported_user.community and target_user.community:
                    if imported_user.community != target_user.community:
                        self.stdout.write(
                            self.style.WARNING(
                                f'    ⚠ Imported user has different community '
                                f'({imported_user.community.slug} vs {target_user.community.slug}), '
                                f'keeping target user\'s community'
                            )
                        )

                # Transfer slot assignments
                slots = MissionSlot.objects.filter(assignee=imported_user)
                slots_count = slots.count()
                if slots_count > 0:
                    slots.update(assignee=target_user)
                    self.stdout.write(
                        f'    Transferred {slots_count} slot assignment(s) from {imported_user.uid}'
                    )

                # Transfer registrations (or delete duplicates)
                registrations = MissionSlotRegistration.objects.filter(user=imported_user)
                reg_count = 0
                dup_count = 0
                
                for reg in registrations:
                    # Check if target user already has a registration for this slot
                    existing = MissionSlotRegistration.objects.filter(
                        user=target_user,
                        slot=reg.slot
                    ).exists()
                    
                    if not existing:
                        reg.user = target_user
                        reg.save()
                        reg_count += 1
                    else:
                        # Delete duplicate registration
                        reg.delete()
                        dup_count += 1
                
                if reg_count > 0:
                    self.stdout.write(
                        f'    Transferred {reg_count} registration(s) from {imported_user.uid}'
                    )
                if dup_count > 0:
                    self.stdout.write(
                        f'    Deleted {dup_count} duplicate registration(s)'
                    )

                # Delete the imported user
                imported_user.delete()
                merged_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'    Deleted imported user {imported_user.uid}')
                )

        return merged_count
