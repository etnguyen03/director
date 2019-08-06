import collections
import os
import threading

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ...users.models import User
from ..database_helpers import create_mysql_database
from ..helpers import (
    add_access_token,
    clean_site_type,
    create_config_files,
    do_git_pull,
    fix_permissions,
    generate_ssh_key,
    generate_ssl_certificate,
    make_site_dirs,
    reload_php_fpm,
    reload_services,
    run_as_site,
)
from ..models import Database, DatabaseHost, Domain, Site


@login_required
def config_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if (
        not request.user.is_superuser
        and not site.group.users.filter(id=request.user.id).exists()
    ):
        raise PermissionDenied

    create_config_files(site)
    reloaded = reload_services()

    if reloaded:
        messages.success(request, "Configuration files regenerated!")
    else:
        messages.error(request, "Failed to reload some services.")
    return redirect("info_site", site_id=site_id)


def fix_permissions_threaded(site):
    t = threading.Thread(target=fix_permissions, args=(site,))
    t.setDaemon(True)
    t.start()


@login_required
def permission_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if (
        not request.user.is_superuser
        and not site.group.users.filter(id=request.user.id).exists()
    ):
        raise PermissionDenied

    make_site_dirs(site)

    fix_permissions_threaded(site)

    messages.success(request, "File permissions regenerated!")
    return redirect("info_site", site_id=site.id)


@require_http_methods(["POST"])
@login_required
def generate_key_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if (
        not request.user.is_superuser
        and not site.group.users.filter(id=request.user.id).exists()
    ):
        raise PermissionDenied

    generate_ssh_key(site)

    messages.success(request, "Generated new RSA public private key-pair!")
    return redirect(
        reverse("info_site", kwargs={"site_id": site_id}) + "#github-manual"
    )


@login_required
def git_pull_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if (
        not request.user.is_superuser
        and not site.group.users.filter(id=request.user.id).exists()
    ):
        raise PermissionDenied

    output = do_git_pull(site)

    return JsonResponse({"ret": output[0], "out": output[1], "err": output[2]})


@login_required
def install_options_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if (
        not request.user.is_superuser
        and not site.group.users.filter(id=request.user.id).exists()
    ):
        raise PermissionDenied

    return render(
        request, "sites/install_options.html", {"site": site, "packages": PACKAGES}
    )


def switch_site_php(site):
    if not site.category == "php":
        site.category = "php"
        site.save()

        clean_site_type(site)
        create_config_files(site)
        reload_services()
    return (True, None)


def provision_mysql_database(site):
    if hasattr(site, "database"):
        if not site.database.category == "mysql":
            return (
                False,
                "A database has already been provisioned and it is not MySQL!",
            )
    else:
        db = Database(
            site=site,
            host=DatabaseHost.objects.filter(dbms="mysql").first(),
            password=User.objects.make_random_password(length=24),
        )
        if create_mysql_database(db):
            db.save()
            create_config_files(site)
            reload_php_fpm()
        else:
            return (False, "Failed to create MySQL database!")
    return (True, None)


PACKAGES = collections.OrderedDict(
    [
        (
            "wordpress",
            {
                "name": "WordPress",
                "icon": "wordpress",
                "description": "WordPress is a free content management system written in PHP and MySQL.",
                "url": "https://wordpress.org/",
                "actions": [
                    ("function", switch_site_php, "Switch site type to PHP"),
                    (
                        "function",
                        provision_mysql_database,
                        "Provision a MySQL database",
                    ),
                    (
                        "terminal",
                        "/scripts/wordpress.sh",
                        "Install Wordpress in the public folder",
                    ),
                ],
            },
        ),
        (
            "drupal",
            {
                "name": "Drupal",
                "icon": "drupal",
                "description": "Drupal is a free content management system written in PHP. It can use both MySQL and PostgreSQL as a database backend.",
                "url": "https://www.drupal.org/",
                "actions": [
                    ("function", switch_site_php, "Switch site type to PHP"),
                    (
                        "function",
                        provision_mysql_database,
                        "Provision a MySQL database",
                    ),
                    (
                        "terminal",
                        "/scripts/drupal.sh",
                        "Install Drupal in the public folder",
                    ),
                ],
            },
        ),
        (
            "joomla",
            {
                "name": "Joomla",
                "icon": "joomla",
                "description": "Joomla is a free content management system written in PHP. It can use both MySQL and PostgreSQL as a database backend.",
                "url": "https://www.joomla.org/",
            },
        ),
    ]
)


@login_required
@add_access_token
def install_package_view(request, site_id, package):
    site = get_object_or_404(Site, id=site_id)
    if (
        not request.user.is_superuser
        and not site.group.users.filter(id=request.user.id).exists()
    ):
        raise PermissionDenied

    if package not in PACKAGES:
        raise Http404

    if request.method == "POST":
        for action in PACKAGES[package]["actions"]:
            if action[0] == "function":
                status, msg = action[1](site)
                if msg:
                    messages.error(request, msg)
                if not status:
                    return redirect("install_package", site_id=site.id, package=package)
            elif action[0] == "terminal":
                return render(
                    request,
                    "sites/web_terminal.html",
                    {"site": site, "command": action[1]},
                )

    return render(
        request,
        "sites/install_package.html",
        {"site": site, "package": PACKAGES[package]},
    )


@csrf_exempt
def webhook_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if request.method == "POST":
        if not request.META["HTTP_USER_AGENT"].startswith("GitHub-Hookshot/"):
            return JsonResponse({"error": "Invalid user agent!"})
        if request.META["HTTP_X_GITHUB_EVENT"] == "ping":
            return JsonResponse({"success": True})
        if not request.META["HTTP_X_GITHUB_EVENT"] == "push":
            return JsonResponse(
                {"error": "Only push events are supported at this time!"}
            )
        output = do_git_pull(site)
        return JsonResponse({"success": bool(output[0] == 0)})
    else:
        return JsonResponse({"error": "Request method not allowed!"})


@require_http_methods(["POST"])
@login_required
def git_setup_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if (
        not request.user.is_superuser
        and not site.group.users.filter(id=request.user.id).exists()
    ):
        raise PermissionDenied

    if not request.user.github_token:
        messages.error(request, "You must connect your GitHub account first!")
    else:
        generate_ssh_key(site, overwrite=False)
        ret, out, err = run_as_site(site, "git remote -v", cwd=site.git_path)
        if ret != 0:
            messages.error(request, "Failed to detect the remote repository!")
        else:
            # Try to identify which remote is the GitHub repository.
            out = [
                [y for y in x.replace("\t", " ").split(" ") if y]
                for x in out.split("\n")
                if x
            ]
            out = [x[1] for x in out if x[2] == "(fetch)"]
            out = [
                x
                for x in out
                if x.startswith("git@github.com") or x.startswith("https://github.com")
            ]
            if not out:
                messages.error(
                    request, "Did not find any remote repositories to pull from!"
                )
            else:
                out = out[0]
                if out.startswith("git@github.com"):
                    out = out.split(":", 1)[1].rsplit(".", 1)[0]
                else:
                    a = out.rsplit("/", 2)
                    out = "{}/{}".format(a[-2], a[-1].rsplit(".", 1)[0])
                repo_info = request.user.github_api_request("/repos/{}".format(out))
                if repo_info is not None:
                    resp = request.user.github_api_request("/repos/{}/keys".format(out))
                    if resp is not None:
                        # Delete all keys from Director that do not match the current key.
                        ssh_rsa, existing_key, existing_host = site.public_key.strip().split(
                            " "
                        )
                        key_exists = False
                        for i in resp:
                            if i["key"].strip().split(" ")[1] == existing_key:
                                key_exists = True
                                continue
                            if i["title"] == "Director":
                                request.user.github_api_request(
                                    "/repos/{}/keys/{}".format(out, i["id"]),
                                    method="DELETE",
                                )

                        # If the key does not already exist in GitHub, add it.
                        if not key_exists:
                            resp = request.user.github_api_request(
                                "/repos/{}/keys".format(out),
                                method="POST",
                                data={
                                    "title": "Director",
                                    "key": site.public_key.strip(),
                                    "read_only": True,
                                },
                            )
                        else:
                            resp = True
                        if resp:
                            # If the webhook does not exist, create it.
                            resp = request.user.github_api_request(
                                "/repos/{}/hooks".format(out)
                            )
                            if resp is not None:
                                webhook_url = request.build_absolute_uri(
                                    reverse("git_webhook", kwargs={"site_id": site_id})
                                ).replace("http://", "https://")
                                for i in resp:
                                    if i["config"]["url"] == webhook_url:
                                        break
                                else:
                                    request.user.github_api_request(
                                        "/repos/{}/hooks".format(out),
                                        method="POST",
                                        data={
                                            "name": "web",
                                            "config": {
                                                "url": webhook_url,
                                                "content_type": "json",
                                            },
                                            "active": True,
                                        },
                                    )
                                messages.success(request, "The integration was set up!")
                            else:
                                messages.error(
                                    request, "Failed to retrieve repository webhooks!"
                                )
                        else:
                            messages.error(request, "Failed to add new deploy key!")
                    else:
                        if not repo_info["permissions"]["admin"]:
                            messages.error(
                                request,
                                "You do not have permission to add deploy keys. Ask the owner of the repository to set this integration up for you.",
                            )
                        else:
                            messages.error(request, "Failed to retrieve deploy keys!")
                else:
                    messages.error(
                        request,
                        "Failed to retrieve repository information from GitHub! Do you have access to this repository?",
                    )

    return redirect(
        reverse("info_site", kwargs={"site_id": site.id}) + "#github-automatic"
    )


@login_required
def set_git_path_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if (
        not request.user.is_superuser
        and not site.group.users.filter(id=request.user.id).exists()
    ):
        raise PermissionDenied

    if request.method == "POST":
        path = request.POST.get("path", site.git_path)

        if not path.startswith(site.path) or not os.path.isdir(path):
            messages.error(request, "You entered a invalid or nonexistent path!")
            return redirect("set_git_path", site_id=site_id)

        site.repo_path = path
        site.save()

        messages.success(request, "The git repository path has been changed!")
        return redirect("info_site", site_id=site_id)

    return render(request, "sites/set_git_path.html", {"site": site})


@require_http_methods(["POST"])
@login_required
def add_ssl_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)

    if (
        not request.user.is_superuser
        and not site.group.users.filter(id=request.user.id).exists()
    ):
        raise PermissionDenied
    name = request.POST.get("domain")
    domain = get_object_or_404(Domain, domain=name)
    if domain.domain.endswith(".sites.tjhsst.edu"):
        return JsonResponse({"success": True})

    t = threading.Thread(target=generate_ssl_certificate, args=(domain,))
    t.daemon = True
    t.start()

    return JsonResponse({"success": True})
    # TODO: allow generating certs for all domains at once.
    # domains = site.domain_set.all()
    # for domain in domains:
    #     generate_ssl_certificate(domain)
    #     return "Hello"
