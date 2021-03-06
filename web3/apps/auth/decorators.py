from django.contrib.auth.decorators import user_passes_test

superuser_required = user_passes_test(lambda u: u.is_authenticated and u.is_superuser)
edit_docs_required = user_passes_test(lambda u: u.is_authenticated and u.can_edit_docs)
