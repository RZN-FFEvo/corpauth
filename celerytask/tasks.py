from django.conf import settings
from celery.task import periodic_task
from django.contrib.auth.models import User

from models import SyncGroupCache
from celery.task.schedules import crontab
from services.managers.openfire_manager import OpenfireManager
from services.managers.mumble_manager import MumbleManager
from services.managers.phpbb3_manager import Phpbb3Manager
from services.managers.ipboard_manager import IPBoardManager
from services.managers.teamspeak3_manager import Teamspeak3Manager
from authentication.models import AuthServicesInfo
from eveonline.managers import EveManager
from services.managers.eve_api_manager import EveApiManager
from util.common_task import deactivate_services
from util.common_task import remove_user_all_groups
from services.managers.slack_manager import SlackManager


def update_jabber_groups(user):
    syncgroups = SyncGroupCache.objects.filter(user=user)
    authserviceinfo = AuthServicesInfo.objects.get(user=user)
    groups = []

    for syncgroup in syncgroups:
        groups.append(str(syncgroup.groupname))

    if len(groups) == 0:
        groups.append('empty')

    print groups

    OpenfireManager.update_user_groups(authserviceinfo.jabber_username, authserviceinfo.jabber_password, groups)


def update_mumble_groups(user):
    syncgroups = SyncGroupCache.objects.filter(user=user)
    authserviceinfo = AuthServicesInfo.objects.get(user=user)
    groups = []
    for syncgroup in syncgroups:
        groups.append(str(syncgroup.groupname))

    if len(groups) == 0:
        groups.append('empty')

    MumbleManager.update_groups(authserviceinfo.mumble_username, groups)


def update_forum_groups(user):
    syncgroups = SyncGroupCache.objects.filter(user=user)
    authserviceinfo = AuthServicesInfo.objects.get(user=user)
    groups = []
    for syncgroup in syncgroups:
        groups.append(str(syncgroup.groupname))

    if len(groups) == 0:
        groups.append('empty')

    Phpbb3Manager.update_groups(authserviceinfo.forum_username, groups)


def update_ipboard_groups(user):
    syncgroups = SyncGroupCache.objects.filter(user=user)
    authserviceinfo = AuthServicesInfo.objects.get(user=user)
    groups = []
    for syncgroup in syncgroups:
        groups.append(str(syncgroup.groupname))

    if len(groups) == 0:
        groups.append('empty')

    IPBoardManager.update_groups(authserviceinfo.ipboard_username, groups)


def update_teamspeak3_groups(user):
    syncgroups = SyncGroupCache.objects.filter(user=user)
    authserviceinfo = AuthServicesInfo.objects.get(user=user)
    groups = []
    for syncgroup in syncgroups:
        groups.append(str(syncgroup.groupname))

    if len(groups) == 0:
        groups.append('empty')

    Teamspeak3Manager.update_groups(authserviceinfo.teamspeak3_uid, groups)


def create_syncgroup_for_user(user, groupname, servicename):
    synccache = SyncGroupCache()
    synccache.groupname = groupname
    synccache.user = user
    synccache.servicename = servicename
    synccache.save()


def remove_all_syncgroups_for_service(user, servicename):
    syncgroups = SyncGroupCache.objects.filter(user=user)
    for syncgroup in syncgroups:
        if syncgroup.servicename == servicename:
            syncgroup.delete()


def add_to_databases(user, groups, syncgroups):
    authserviceinfo = None
    try:
        authserviceinfo = AuthServicesInfo.objects.get(user=user)
    except:
        pass

    if authserviceinfo:
        authserviceinfo = AuthServicesInfo.objects.get(user=user)

        for group in groups:

            if authserviceinfo.jabber_username and authserviceinfo.jabber_username != "":
                if syncgroups.filter(groupname=group.name).filter(servicename="openfire").exists() is not True:
                    create_syncgroup_for_user(user, group.name, "openfire")
                    update_jabber_groups(user)
            if authserviceinfo.mumble_username and authserviceinfo.mumble_username != "":
                if syncgroups.filter(groupname=group.name).filter(servicename="mumble").exists() is not True:
                    create_syncgroup_for_user(user, group.name, "mumble")
                    update_mumble_groups(user)
            if authserviceinfo.forum_username and authserviceinfo.forum_username != "":
                if syncgroups.filter(groupname=group.name).filter(servicename="phpbb3").exists() is not True:
                    create_syncgroup_for_user(user, group.name, "phpbb3")
                    update_forum_groups(user)
            if authserviceinfo.ipboard_username and authserviceinfo.ipboard_username != "":
                if syncgroups.filter(groupname=group.name).filter(servicename="ipboard").exists() is not True:
                    create_syncgroup_for_user(user, group.name, "ipboard")
                    update_ipboard_groups(user)
            if authserviceinfo.teamspeak3_uid and authserviceinfo.teamspeak3_uid != "":
                if syncgroups.filter(groupname=group.name).filter(servicename="teamspeak3").exists() is not True:
                    create_syncgroup_for_user(user, group.name, "teamspeak3")
                    update_teamspeak3_groups(user)


def remove_from_databases(user, groups, syncgroups):
    authserviceinfo = None
    try:
        authserviceinfo = AuthServicesInfo.objects.get(user=user)
    except:
        pass

    if authserviceinfo:
        update = False
        for syncgroup in syncgroups:
            group = groups.filter(name=syncgroup.groupname)

            if not group:
                syncgroup.delete()
                update = True

        if update:
            if authserviceinfo.jabber_username and authserviceinfo.jabber_username != "":
                update_jabber_groups(user)
            if authserviceinfo.mumble_username and authserviceinfo.mumble_username != "":
                update_mumble_groups(user)
            if authserviceinfo.forum_username and authserviceinfo.forum_username != "":
                update_forum_groups(user)
            if authserviceinfo.ipboard_username and authserviceinfo.ipboard_username != "":
                update_ipboard_groups(user)
            if authserviceinfo.teamspeak3_uid and authserviceinfo.teamspeak3_uid != "":
                update_teamspeak3_groups(user)


# Run every minute
@periodic_task(run_every=crontab(minute="*/1"))
def run_databaseUpdate():
    users = User.objects.all()
    for user in users:
        groups = user.groups.all()
        syncgroups = SyncGroupCache.objects.filter(user=user)
        add_to_databases(user, groups, syncgroups)
        remove_from_databases(user, groups, syncgroups)

    # no point if slack isn't enabled
    # this isn't really going to run every minute
    # cache will stop it
    if SlackManager.enabled():
        if EveApiManager.check_if_api_server_online():
            kill_api = EveApiManager.get_corp_kills(settings.ALLIANCE_EXEC_CORP_ID, settings.ALLIANCE_EXEC_CORP_VCODE)
            for kill in kill_api.result:
                if not EveManager.check_corporation_kill(kill):
                    # if sent save to db
                    if SlackManager.send_kill(kill):
                        EveManager.create_corporation_kill(kill)


def prime_kills():
    if EveApiManager.check_if_api_server_online():
        kill_api = EveApiManager.get_corp_kills(settings.ALLIANCE_EXEC_CORP_ID, settings.ALLIANCE_EXEC_CORP_VCODE)
        for kill in kill_api.result:
            EveManager.create_corporation_kill(kill)


# Run every 3 hours
@periodic_task(run_every=crontab(minute=0, hour="*/3"))
def run_api_refresh():

    users = User.objects.all()

    for user in users:
        # Check if the api server is online
        if EveApiManager.check_if_api_server_online():
            api_key_pairs = EveManager.get_api_key_pairs(user.id)
            if api_key_pairs:
                authserviceinfo = AuthServicesInfo.objects.get(user=user)

                if settings.DEBUG:
                    print 'Running update on user: ' + user.username
                if authserviceinfo.main_char_id and authserviceinfo.main_char_id != "":
                    for api_key_pair in api_key_pairs:
                        if settings.DEBUG:
                            print 'Running on ' + api_key_pair.api_id + ':' + api_key_pair.api_key
                        if EveApiManager.api_key_is_valid(api_key_pair.api_id, api_key_pair.api_key):
                            # Update characters
                            characters = EveApiManager.get_characters_from_api(api_key_pair.api_id,
                                                                               api_key_pair.api_key)
                            EveManager.update_characters_from_list(characters)
                            # Check our main character
                            character = EveManager.get_character_by_id(authserviceinfo.main_char_id)
                            main_alliance_id = EveManager.get_charater_corporation_id_by_id(
                                authserviceinfo.main_char_id)

                            # NPC corps return as None
                            if main_alliance_id is None or int(main_alliance_id) != int(settings.ALLIANCE_ID):
                                if settings.DEBUG:
                                    print 'Not in Corp'

                                SlackManager.send_director('API ERROR: ' + user.username +
                                                           ' Not in corp.\n\tServices disabled.\n\tAPI removed.')

                                remove_user_all_groups(user)
                                deactivate_services(user)
                                EveManager.delete_characters_by_api_id(api_key_pair.api_id, user.id)
                                EveManager.delete_api_key_pair(api_key_pair.api_id, user.id)
                        else:
                            if settings.DEBUG:
                                print 'Bad API Deleting character and api for ' + user.username

                            SlackManager.send_director('API ERROR: Bad API for user ' + user.username +
                                                       '\n\tServices disabled.\n\tAPI removed.')

                            remove_user_all_groups(user)
                            deactivate_services(user)
                            EveManager.delete_characters_by_api_id(api_key_pair.api_id, user.id)
                            EveManager.delete_api_key_pair(api_key_pair.api_id, user.id)

                else:
                    if settings.DEBUG:
                        print 'No main_char_id set'
                        # SlackManager.send_director('API ERROR: No main character set for user ' + user.username)


# Run Every 2 hours
@periodic_task(run_every=crontab(minute=0, hour="*/24"))
def run_alliance_corp_update():
    # I am not proud of this block of code
    if EveApiManager.check_if_api_server_online():
        # Get Corp info
        corp_info = EveApiManager.get_corporation_information(settings.ALLIANCE_ID, settings.ALLIANCE_EXEC_CORP_ID,
                                                              settings.ALLIANCE_EXEC_CORP_VCODE)

        # Dummy alliance info
        if not EveManager.check_if_alliance_exists_by_id(settings.ALLIANCE_ID):
            EveManager.create_alliance_info(settings.ALLIANCE_ID, corp_info['name'], corp_info['ticker'],
                                            settings.ALLIANCE_ID, 1, False)
        else:
            # Update semi fake data no real point
            EveManager.update_alliance_info(settings.ALLIANCE_ID, settings.ALLIANCE_ID,
                                            1, False)

        # Get the fake data we just added / updated
        alliance = EveManager.get_alliance_info_by_id(settings.ALLIANCE_ID)

        # Only one corp add or update
        if not EveManager.check_if_corporation_exists_by_id(corp_info['id']):
            EveManager.create_corporation_info(corp_info['id'], corp_info['name'], corp_info['ticker'],
                                               corp_info['members']['current'], False, alliance)
        else:
            EveManager.update_corporation_info(corp_info['id'], corp_info['members']['current'], alliance,
                                               False)
