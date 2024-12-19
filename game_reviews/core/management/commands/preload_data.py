import random
from django.core.management.base import BaseCommand
from core.models import CustomUser, Game, Platform, Category, Tag, Review
from django.utils.timezone import now

class Command(BaseCommand):
    help = 'Preload initial data into the database'

    def handle(self, *args, **kwargs):
        # Create admin user
        admin_user, created = CustomUser.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'role': 'admin',
                'is_superuser': True,
                'is_staff': True,
            }
        )
        if created:
            admin_user.set_password('adminpassword')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Admin user created'))

        # Create moderator
        moderator_user, created = CustomUser.objects.get_or_create(
            username='moderator',
            defaults={
                'email': 'moderator@example.com',
                'role': 'moderator',
            }
        )
        if created:
            moderator_user.set_password('moderatorpassword')
            moderator_user.save()
            self.stdout.write(self.style.SUCCESS('Moderator user created'))

        # Create two critics
        critic1_user, created = CustomUser.objects.get_or_create(
            username='critic1',
            defaults={
                'email': 'critic1@example.com',
                'role': 'critic',
            }
        )
        if created:
            critic1_user.set_password('critic1password')
            critic1_user.save()
            self.stdout.write(self.style.SUCCESS('Critic 1 user created'))

        critic2_user, created = CustomUser.objects.get_or_create(
            username='critic2',
            defaults={
                'email': 'critic2@example.com',
                'role': 'critic',
            }
        )
        if created:
            critic2_user.set_password('critic2password')
            critic2_user.save()
            self.stdout.write(self.style.SUCCESS('Critic 2 user created'))

        # Add some platforms
        platforms = ['PC', 'PlayStation', 'Xbox', 'Nintendo']
        for platform_name in platforms:
            Platform.objects.get_or_create(platform_name=platform_name)
        self.stdout.write(self.style.SUCCESS('Platforms added'))

        # Add some categories
        categories = ['Action', 'Adventure', 'RPG', 'Strategy']
        for category_name in categories:
            Category.objects.get_or_create(category_name=category_name)
        self.stdout.write(self.style.SUCCESS('Categories added'))

        # Add some tags
        tags = ['Multiplayer', 'Singleplayer', 'Co-op', 'VR']
        for tag_name in tags:
            Tag.objects.get_or_create(tag_name=tag_name)
        self.stdout.write(self.style.SUCCESS('Tags added'))

        # Create some games
        games = [
            {
                'title': 'Game 1',
                'description': 'First game description',
                'developer': 'Dev Studio 1',
                'publisher': 'Publisher 1',
                'release_date': now().date(),
                'age_rating': 18,
                'genre': 'Action',
            },
            {
                'title': 'Game 2',
                'description': 'Second game description',
                'developer': 'Dev Studio 2',
                'publisher': 'Publisher 2',
                'release_date': now().date(),
                'age_rating': 16,
                'genre': 'Adventure',
            },
            {
                'title': 'Game 3',
                'description': 'Third game description',
                'developer': 'Dev Studio 3',
                'publisher': 'Publisher 3',
                'release_date': now().date(),
                'age_rating': 12,
                'genre': 'RPG',
            },
            {
                'title': 'Game 4',
                'description': 'Fourth game description',
                'developer': 'Dev Studio 4',
                'publisher': 'Publisher 4',
                'release_date': now().date(),
                'age_rating': 10,
                'genre': 'Strategy',
            },
            {
                'title': 'Game 5',
                'description': 'Fifth game description',
                'developer': 'Dev Studio 5',
                'publisher': 'Publisher 5',
                'release_date': now().date(),
                'age_rating': 14,
                'genre': 'Action',
            },
        ]

        created_games = []
        for game_data in games:
            game, created = Game.objects.get_or_create(
                title=game_data['title'],
                defaults=game_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Game '{game.title}' created"))
            created_games.append(game)

        # Define random review data
        ratings = [1, 2, 3, 4, 5]
        review_titles = [
            "Amazing game!",
            "Pretty good",
            "It was okay",
            "Not great",
            "Terrible experience",
        ]
        review_comments = [
            "Loved this game so much!",
            "Had a fun time playing.",
            "It could have been better.",
            "Disappointing experience.",
            "I would not recommend this game.",
        ]

        # Add random reviews for the games (only by critics)
        for game in created_games:
            for critic_user in [critic1_user, critic2_user]:
                Review.objects.get_or_create(
                    game=game,
                    user=critic_user,
                    defaults={
                        'rating': random.choice(ratings),
                        'title': random.choice(review_titles),
                        'comment': random.choice(review_comments),
                    }
                )

        self.stdout.write(self.style.SUCCESS('Random reviews added (by critics only)'))
        self.stdout.write(self.style.SUCCESS('Initial data preloaded'))
