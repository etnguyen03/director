import os
import shutil
import stat
from subprocess import Popen, check_output

from .models import Site
from ..users.models import User, Group

from django.template.loader import render_to_string


def create_site_users(site):
    try:
        user = User.objects.get(username="site_{}".format(site.name))
    except User.DoesNotExist:
        user = User.objects.create(id=get_next_id(), service=True, username="site_{}".format(site.name), email="site_{}@tjhsst.edu".format(site.name))
    try:
        group = Group.objects.get(name="site_{}".format(site.name))
    except Group.DoesNotExist:
        group = Group.objects.create(id=user.id, service=True, name="site_{}".format(site.name))
        group.users.add(user)
        group.save()
    site.user = user
    site.group = group
    site.save()
    return (user, group)


def get_next_id():
    if User.objects.filter(service=True).count() == 0:
        return 10000
    return list(User.objects.filter(service=True).order_by('id'))[-1].id + 1


def make_site_dirs(site):
    for i in ["{}", "{}public", "{}private"]:
        path = i.format(site.path)
        if not os.path.exists(path):
            os.makedirs(path)
        os.chown(path, site.user.id, site.group.id)
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
                 | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP
                 | stat.S_ISGID)
    Popen("/usr/bin/setfacl -m u:www-data:rx {}".format(site.path).split())
    Popen("/usr/bin/setfacl -m u:www-data:rx {}public".format(site.path).split())


def create_config_files(site):
    if not site.custom_nginx:
        with open("/etc/nginx/director.d/{}.conf".format(site.name), "w+") as f:
            f.write(render_to_string("config/nginx.conf", {"site": site}))
    if site.category == "php":
        with open("/etc/php5/fpm/pool.d/{}.conf".format(site.name), "w+") as f:
            f.write(render_to_string("config/phpfpm.conf", {"site": site}))


def delete_site_files(site):
    files = ["/etc/nginx/director.d/{}.conf", "/etc/php5/fpm/pool.d/{}.conf"]
    files = [x.format(site.name) for x in files]
    for f in files:
        if os.path.isfile(f):
            os.remove(f)
    shutil.rmtree(site.path)


def create_process_config(process):
    with open("/etc/supervisor/director.d/{}.conf".format(process.site.name), "w+") as f:
        f.write(render_to_string("config/supervisor.conf", {"process": process}))


def delete_process_config(process):
    filename = "/etc/supervisor/director.d/{}.conf".format(process.site.name)
    if os.path.isfile(filename):
        os.remove(filename)


def restart_supervisor(site):
    try:
        site.process
        Popen("supervisorctl restart {}".format(site.name).split())
    except Site.process.RelatedObjectDoesNotExist:
        pass


def get_supervisor_status(site):
    try:
        site.process
        return check_output("supervisorctl status {}".format(site.name).split()).decode()
    except Site.process.RelatedObjectDoesNotExist:
        return "No Process"


def reload_services():
    Popen("systemctl reload nginx.service".split())
    Popen("systemctl restart php5-fpm.service".split())
    Popen("supervisorctl update".split())
