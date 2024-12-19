from django.core.management.base import BaseCommand
from core.models import Tag, Category, Platform

class Command(BaseCommand):
    help = "Add initial data for tags, categories, and platforms"

    def handle(self, *args, **kwargs):
        # Add Tags
        tags = ["Action", "Adventure", "RPG", "Strategy"]
        for tag_name in tags:
            Tag.objects.get_or_create(tag_name=tag_name)

        # Add Categories
        categories = ["Single-player", "Multiplayer", "Co-op"]
        for category_name in categories:
            Category.objects.get_or_create(category_name=category_name)

        # Add Platforms
        platforms = ["PC", "Xbox", "PlayStation", "Nintendo"]
        for platform_name in platforms:
            Platform.objects.get_or_create(platform_name=platform_name)

        self.stdout.write(self.style.SUCCESS("Data added successfully!"))
