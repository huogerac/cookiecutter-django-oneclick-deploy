import platform
from fabric.api import env, sudo, run, cd, prefix, require
from fabric.colors import green, red
from fabric.utils import abort

from os import environ, pardir
from os.path import abspath, basename, dirname, join, normpath, exists, isdir
from sys import path

BASE_DIR = dirname(__file__)  #Project or Repo Base Dir
VIRTUALENV_DIR = dirname(dirname(__file__))

REPO_FOLDER_NAME = '{{cookiecutter.project_name}}'
PROJECT_NAME = '{{cookiecutter.project_name}}'
PROJECT_REPO = '{{cookiecutter.repository_url}}'

NGINX_TARGET_FOLDER = '/etc/nginx'
GUNICORN_TARGET_FOLDER = '/etc/init'



def __get_env_pass__(environment):
    pass_env_var_name = '%s_%s' % (PROJECT_NAME.upper().replace('-', ''), environment.upper())
    pass_env_var = environ.get(pass_env_var_name)
    if not pass_env_var:
        abort('You must set up the password using the SO variable: %s' % pass_env_var_name)
    return pass_env_var

def {{cookiecutter.environment}}():
    "Setup {{cookiecutter.environment}} server"
    env.environment = '{{cookiecutter.environment}}'
    env.dev_mode = False
    env.targetdir = '{{cookiecutter.targetdir}}'
    env.server_url = '{{cookiecutter.server_url}}'
    env.user = '{{cookiecutter.user}}'
    env.password = __get_env_pass__(env.environment)
    env.hosts = env.server_url.split()


def _create_virtualenv(targetdir, virtualenv_folder):
    print(green("\n\n**** Creating virtualenv"))
    with cd(targetdir):
        run_cmd = "virtualenv {0}".format(virtualenv_folder)
        print(green("$ {0}\n".format(run_cmd) ))
        run(run_cmd)

def _clone_repository(targetdir, virtualenv_folder ):
    print(green("\n\n**** Cloning Repository"))
    with cd(targetdir):
        run_cmd = "cd {0}; git clone {1} {2}".format(virtualenv_folder, PROJECT_REPO, REPO_FOLDER_NAME)
        print(green("$ {0}\n".format(run_cmd) ))
        run(run_cmd)

def _install_project_dependencies(projectdir):
    print(green("\n\n**** Installing project dependencies"))
    with cd(projectdir):
        with prefix('source ../bin/activate'):
            run_cmd = 'pip install -r requirements/{0}.pip'.format(env.environment)
            print(green("$ {0}\n".format(run_cmd) ))
            run(run_cmd)

def _prepare_database(projectdir):
    print(green("\n\n**** Preparing Database"))
    with cd(projectdir):
        with prefix('source ../bin/activate'):
            # run_cmd = './manage.py migrate --settings={0}.settings.{1}'.format(PROJECT_NAME, env.environment)
            run_cmd = './manage.py migrate'
            print(green("$ {0}\n".format(run_cmd) ))
            run(run_cmd)

def _prepare_log_folder(targetdir, virtualenv_folder):
    print(green("**** Preparing Log folder"))
    with cd(targetdir):
        run_cmd = 'mkdir -p {0}/logs'.format(virtualenv_folder)
        print(green("$ {0}\n".format(run_cmd) ))
        run(run_cmd)


def _update_server_files(projectdir):
    print(green("**** Updating NGINX and GUNICORN"))
    newentry_filename = '{0}_{1}'.format(PROJECT_NAME, env.environment)
    with cd(projectdir):
        run('cp deploy/config/nginx.{0} {1}/sites-available/{2}'.format(env.environment, NGINX_TARGET_FOLDER, newentry_filename))
        run('cp deploy/config/gunicorn.{0} {1}/gunicorn-{2}.conf'.format(env.environment, GUNICORN_TARGET_FOLDER, newentry_filename))

    with cd(NGINX_TARGET_FOLDER + '/sites-enabled/'):
        run('rm -f {0}'.format(newentry_filename)
        run('ln -s {0}'.format(
            NGINX_TARGET_FOLDER + '/sites-enabled/' + newentry_filename)


def bootstrap():
    print(green("Bootstrap:: targetdir=%s" % env.targetdir))

    virtualenv_folder = "%s_%s" % (PROJECT_NAME, env.environment)
    repodir = join(env.targetdir, virtualenv_folder, REPO_FOLDER_NAME)
    projectdir = repodir  # join(repodir, PROJECT_NAME)

    _create_virtualenv(env.targetdir, virtualenv_folder)
    _clone_repository(env.targetdir, virtualenv_folder)
    _install_project_dependencies(projectdir)
    _prepare_database(projectdir)
    if not env.dev_mode:
        _update_server_files(projectdir)
        _prepare_log_folder(env.targetdir, virtualenv_folder)

    print(green("bootstrap DONE"))




def _update_code(projectdir):
    print(green("**** Updating repository"))
    with cd(projectdir):
        run("git pull")

def _migrate_database(projectdir):
    print(green("**** Migrating Database"))
    with cd(projectdir):
        with prefix('source ../../bin/activate'):
            run('./manage.py migrate --settings=%s.settings.%s' % (PROJECT_NAME, env.environment))

def _update_assets(projectdir):
    print(green("**** Updating Assets (static files)"))
    with cd(projectdir):
        with prefix('source ../../bin/activate'):
            run('./manage.py collectstatic --noinput --settings=%s.settings.%s' % (PROJECT_NAME, env.environment))

def _reload_servers():
    print(green("**** Reloading servers (NGINX, GUNICORN"))
    GUNICORN_SERVICE = "gunicorn-%s_%s" % (PROJECT_NAME, env.environment)
    NGINX_SERVICE = "nginx"
    try:
        sudo("reload %s" % GUNICORN_SERVICE)
    except:
        sudo("start %s" % GUNICORN_SERVICE)
    sudo("service %s reload" % NGINX_SERVICE)


def deploy():
    print(green("Deploying :: %s (%s)" % (env.environment, env.server_url)))

    virtualenv_folder = "%s_%s" % (PROJECT_NAME, env.environment)
    repodir = join(env.targetdir, virtualenv_folder, REPO_FOLDER_NAME)
    projectdir = join(repodir, PROJECT_NAME)

    _update_code(projectdir)
    _install_project_dependencies(projectdir)
    _migrate_database(projectdir)
    if not env.dev_mode:
        _update_assets(projectdir)
        _reload_servers()

    print(green("Deploy DONE"))