# SCP-079-CLEAN - Filter specific types of messages
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-CLEAN.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import re
from typing import Union

from pyrogram import Client, Filters, Message

from .. import glovar
from .channel import get_content
from .etc import get_channel_link, get_command_type, get_entity_text, get_now, get_links, get_stripped_link, get_text
from .file import delete_file, get_downloaded_path, save
from .group import get_description, get_group_sticker, get_pinned
from .ids import init_group_id
from .image import get_file_id, get_qrcode
from .telegram import get_chat_member, resolve_username

# Enable logging
logger = logging.getLogger(__name__)


def is_class_c(_, message: Message) -> bool:
    # Check if the message is Class C object
    try:
        if message.from_user:
            uid = message.from_user.id
            gid = message.chat.id
            if init_group_id(gid):
                if uid in glovar.admin_ids[gid] or uid in glovar.bot_ids or message.from_user.is_self:
                    return True
    except Exception as e:
        logger.warning(f"Is class c error: {e}", exc_info=True)

    return False


def is_class_d(_, message: Message) -> bool:
    # Check if the message is Class D object
    try:
        if message.from_user:
            uid = message.from_user.id
            if uid in glovar.bad_ids["users"]:
                return True

        if message.forward_from:
            fid = message.forward_from.id
            if fid in glovar.bad_ids["users"]:
                return True

        if message.forward_from_chat:
            cid = message.forward_from_chat.id
            if cid in glovar.bad_ids["channels"]:
                return True
    except Exception as e:
        logger.warning(f"Is class d error: {e}", exc_info=True)

    return False


def is_class_e(_, message: Message) -> bool:
    # Check if the message is Class E object
    try:
        if message.forward_from_chat:
            cid = message.forward_from_chat.id
            if cid in glovar.except_ids["channels"]:
                return True

        if message.game:
            short_name = message.game.short_name
            if short_name in glovar.except_ids["long"]:
                return True

        content = get_content(message)
        if content:
            if (content in glovar.except_ids["long"]
                    or content in glovar.except_ids["temp"]):
                return True
    except Exception as e:
        logger.warning(f"Is class e error: {e}", exc_info=True)

    return False


def is_declared_message(_, message: Message) -> bool:
    # Check if the message is declared by other bots
    try:
        if message.chat:
            gid = message.chat.id
            mid = message.message_id
            return is_declared_message_id(gid, mid)
    except Exception as e:
        logger.warning(f"Is declared message error: {e}", exc_info=True)

    return False


def is_exchange_channel(_, message: Message) -> bool:
    # Check if the message is sent from the exchange channel
    try:
        if message.chat:
            cid = message.chat.id
            if glovar.should_hide:
                if cid == glovar.hide_channel_id:
                    return True
            elif cid == glovar.exchange_channel_id:
                return True
    except Exception as e:
        logger.warning(f"Is exchange channel error: {e}", exc_info=True)

    return False


def is_from_user(_, message: Message) -> bool:
    # Check if the message is sent from a user
    try:
        if message.from_user:
            return True
    except Exception as e:
        logger.warning(f"Is from user error: {e}", exc_info=True)

    return False


def is_hide_channel(_, message: Message) -> bool:
    # Check if the message is sent from the hide channel
    try:
        if message.chat:
            cid = message.chat.id
            if cid == glovar.hide_channel_id:
                return True
    except Exception as e:
        logger.warning(f"Is hide channel error: {e}", exc_info=True)

    return False


def is_new_group(_, message: Message) -> bool:
    # Check if the bot joined a new group
    try:
        if message.new_chat_members:
            new_users = message.new_chat_members
            if new_users:
                for user in new_users:
                    if user.is_self:
                        return True
        elif message.group_chat_created or message.supergroup_chat_created:
            return True
    except Exception as e:
        logger.warning(f"Is new group error: {e}", exc_info=True)

    return False


def is_test_group(_, message: Message) -> bool:
    # Check if the message is sent from the test group
    try:
        if message.chat:
            cid = message.chat.id
            if cid == glovar.test_group_id:
                return True
    except Exception as e:
        logger.warning(f"Is test group error: {e}", exc_info=True)

    return False


class_c = Filters.create(
    func=is_class_c,
    name="Class C"
)

class_d = Filters.create(
    func=is_class_d,
    name="Class D"
)

class_e = Filters.create(
    func=is_class_e,
    name="Class E"
)

declared_message = Filters.create(
    func=is_declared_message,
    name="Declared message"
)

exchange_channel = Filters.create(
    func=is_exchange_channel,
    name="Exchange Channel"
)

from_user = Filters.create(
    func=is_from_user,
    name="From User"
)

hide_channel = Filters.create(
    func=is_hide_channel,
    name="Hide Channel"
)

new_group = Filters.create(
    func=is_new_group,
    name="New Group"
)

test_group = Filters.create(
    func=is_test_group,
    name="Test Group"
)


def is_ban_text(text: str) -> bool:
    # Check if the text is ban text
    try:
        if is_regex_text("ban", text):
            return True

        if is_regex_text("ad", text) and (is_regex_text("con", text) or is_regex_text("iml", text)):
            return True
    except Exception as e:
        logger.warning(f"Is ban text error: {e}", exc_info=True)

    return False


def is_bmd(message: Message) -> bool:
    # Check if the message is bot command:
    try:
        text = get_text(message)
        if (re.search("^/[a-z]|^/$", text, re.I) and "/" not in text.split(" ")[0][1:]
                and not any([re.search(f"^/{c}$", text) for c in glovar.other_commands])):
            if not get_command_type(message):
                return True
    except Exception as e:
        logger.warning(f"Is bmd error: {e}", exc_info=True)

    return False


def is_declared_message_id(gid: int, mid: int) -> bool:
    # Check if the message's ID is declared by other bots
    try:
        if mid in glovar.declared_message_ids.get(gid, set()):
            return True
    except Exception as e:
        logger.warning(f"Is declared message id error: {e}", exc_info=True)

    return False


def is_delete_text(text: str) -> bool:
    # Check if the text is delete text
    try:
        if is_regex_text("del", text):
            return True

        if is_regex_text("spc", text):
            return True

        if is_regex_text("spe", text):
            return True
    except Exception as e:
        logger.warning(f"Is delete text error: {e}", exc_info=True)

    return False


def is_detected_url(message: Message) -> str:
    # Check if the message include detected url, return detected type
    try:
        if is_class_c(None, message):
            return ""

        gid = message.chat.id
        links = get_links(message)
        for link in links:
            detected_type = glovar.contents.get(link, "")
            if detected_type and is_in_config(gid, detected_type):
                return detected_type
    except Exception as e:
        logger.warning(f"Is detected url error: {e}", exc_info=True)

    return ""


def is_detected_user(message: Message) -> bool:
    # Check if the message is sent by a detected user
    try:
        if message.from_user:
            gid = message.chat.id
            uid = message.from_user.id
            return is_detected_user_id(gid, uid)
    except Exception as e:
        logger.warning(f"Is detected user error: {e}", exc_info=True)

    return False


def is_detected_user_id(gid: int, uid: int) -> bool:
    # Check if the user_id is detected in the group
    try:
        user = glovar.user_ids.get(uid, {})
        if user:
            status = user["detected"].get(gid, 0)
            now = get_now()
            if now - status < glovar.punish_time:
                return True
    except Exception as e:
        logger.warning(f"Is detected user id error: {e}", exc_info=True)

    return False


def is_exe(message: Message) -> bool:
    # Check if the message contain a exe
    try:
        extensions = ["apk", "bat", "cmd", "com", "exe", "msi", "pif", "scr", "vbs"]
        if message.document:
            if message.document.file_name:
                file_name = message.document.file_name
                for file_type in extensions:
                    if re.search(f"[.]{file_type}$", file_name, re.I):
                        return True

            if message.document.mime_type:
                mime_type = message.document.mime_type
                if "application/x-ms" in mime_type or "executable" in mime_type:
                    return True

        extensions.remove("com")
        links = get_links(message)
        for link in links:
            for file_type in extensions:
                if re.search(f"[.]{file_type}$", link, re.I):
                    return True
    except Exception as e:
        logger.warning(f"Is exe error: {e}", exc_info=True)

    return False


def is_high_score_user(message: Message) -> Union[bool, float]:
    # Check if the message is sent by a high score user
    try:
        if message.from_user:
            uid = message.from_user.id
            user = glovar.user_ids.get(uid, {})
            if user:
                score = sum(user["score"].values())
                if score >= 3.0:
                    return score
    except Exception as e:
        logger.warning(f"Is high score user error: {e}", exc_info=True)

    return False


def is_in_config(gid: int, the_type: str) -> bool:
    # Check if the type is in the group's config
    try:
        if glovar.configs.get(gid, {}):
            return glovar.configs[gid].get(the_type, False)
    except Exception as e:
        logger.warning(f"Is in config error: {e}", exc_info=True)

    return False


def is_not_allowed(client: Client, message: Message, text: str = None, image_path: str = None) -> str:
    # Check if the message is not allowed in the group
    result = ""
    if image_path:
        need_delete = [image_path]
    else:
        need_delete = []

    try:
        gid = message.chat.id

        # Regular message
        if not (text or image_path):
            # Bypass
            message_content = get_content(message)
            description = get_description(client, gid)
            if (description and message_content) and message_content in description:
                return ""

            pinned_message = get_pinned(client, gid)
            pinned_content = get_text(pinned_message)
            if (pinned_content and message_content) and message_content in pinned_content:
                return ""

            group_sticker = get_group_sticker(client, gid)
            if message.sticker:
                sticker_name = message.sticker.set_name
                if sticker_name == group_sticker:
                    return ""

            # Check detected records
            if not is_class_c(None, message):
                # If the user is being punished
                if is_detected_user(message):
                    return "true"

                # If the message has been detected
                if message_content:
                    detection = glovar.contents.get(message_content, "")
                    if detection and is_in_config(gid, detection):
                        return detection

            # Privacy messages

            # Contact
            if is_in_config(gid, "con"):
                if message.contact:
                    return "con"

            # Location
            if is_in_config(gid, "loc"):
                if message.location or message.venue:
                    return "loc"

            # Video note
            if is_in_config(gid, "vdn"):
                if message.video_note:
                    return "vdn"

            # Voice
            if is_in_config(gid, "voi"):
                if message.voice:
                    return "voi"

            # Basic types messages

            # Bot command
            if is_in_config(gid, "bmd"):
                if is_bmd(message):
                    return "bmd"

            if not is_class_c(None, message):
                # Animated Sticker
                if is_in_config(gid, "ast"):
                    if message.sticker and message.sticker.is_animated:
                        return "ast"

                # Audio
                if is_in_config(gid, "aud"):
                    if message.audio:
                        return "aud"

                # Document
                if is_in_config(gid, "doc"):
                    if message.document:
                        return "doc"

                # Game
                if is_in_config(gid, "gam"):
                    if message.game:
                        return "gam"

                # GIF
                if is_in_config(gid, "gif"):
                    if (message.animation
                            or (message.document
                                and message.document.mime_type
                                and "gif" in message.document.mime_type)):
                        return "gif"

                # Via Bot
                if is_in_config(gid, "via"):
                    if message.via_bot:
                        return "via"

                # Video
                if is_in_config(gid, "vid"):
                    if message.video:
                        return "vid"

                # Service
                if is_in_config(gid, "ser"):
                    if message.service:
                        return "ser"

                # Sticker
                if is_in_config(gid, "sti"):
                    return "sti"

            # Spam messages

            if not (is_class_c(None, message) or is_class_e(None, message)):
                message_text = get_text(message)

                # AFF link
                if is_in_config(gid, "aff"):
                    if is_regex_text("aff", message_text):
                        return "aff"

                # Executive file
                if is_in_config(gid, "exe"):
                    if is_exe(message):
                        return "exe"

                # Instant messenger link
                if is_in_config(gid, "iml"):
                    if is_regex_text("iml", message_text):
                        return "iml"

                # Short link
                if is_in_config(gid, "sho"):
                    if is_regex_text("sho", message_text):
                        return "sho"

                # Telegram link
                if is_in_config(gid, "tgl"):
                    if is_tgl(client, message):
                        return "tgl"

                # Telegram proxy
                if is_in_config(gid, "tgp"):
                    if is_regex_text("tgp", message_text):
                        return "tgp"

                # QR code
                if is_in_config(gid, "qrc"):
                    file_id, file_ref, big = get_file_id(message)
                    if big:
                        image_path = get_downloaded_path(client, file_id, file_ref)
                        if is_declared_message(None, message):
                            return ""
                        elif image_path:
                            need_delete.append(image_path)
                            qrcode = get_qrcode(image_path)
                            if qrcode and not (glovar.nospam_id in glovar.admin_ids[gid] and is_ban_text(qrcode)):
                                return "qrc"

            # Schedule to delete stickers and animations
            if (message.sticker
                    or message.animation
                    or (message.document
                        and message.document.mime_type
                        and "gif" in message.document.mime_type)):
                mid = message.message_id
                glovar.message_ids[gid]["stickers"][mid] = get_now()
                save("message_ids")
                return ""

        # Preview message
        else:
            if text:
                # AFF link
                if is_in_config(gid, "aff"):
                    if is_regex_text("aff", text):
                        return "aff"

                # Instant messenger link
                if is_in_config(gid, "iml"):
                    if is_regex_text("iml", text):
                        return "iml"

                # Short link
                if is_in_config(gid, "sho"):
                    if is_regex_text("sho", text):
                        return "sho"

                # Telegram link
                if is_in_config(gid, "tgl"):
                    if is_regex_text("tgl", text):
                        return "tgl"

                # Telegram proxy
                if is_in_config(gid, "tgp"):
                    if is_regex_text("tgp", text):
                        return "tgp"

            # QR code
            if image_path:
                qrcode = get_qrcode(image_path)
                if qrcode and not (glovar.nospam_id in glovar.admin_ids[gid] and is_ban_text(qrcode)):
                    return "qrc"
    except Exception as e:
        logger.warning(f"Is not allowed error: {e}", exc_info=True)
    finally:
        for file in need_delete:
            delete_file(file)

    return result


def is_regex_text(word_type: str, text: str, again: bool = False) -> bool:
    # Check if the text hit the regex rules
    result = False
    try:
        if text:
            if not again:
                text = re.sub(r"\s{2,}", " ", text)
            elif " " in text:
                text = re.sub(r"\s", "", text)
            else:
                return False
        else:
            return False

        for word in list(eval(f"glovar.{word_type}_words")):
            if re.search(word, text, re.I | re.S | re.M):
                result = True

            # Match, count and return
            if result:
                count = eval(f"glovar.{word_type}_words").get(word, 0)
                count += 1
                eval(f"glovar.{word_type}_words")[word] = count
                save(f"{word_type}_words")
                return result

        # Try again
        return is_regex_text(word_type, text, True)
    except Exception as e:
        logger.warning(f"Is regex text error: {e}", exc_info=True)

    return result


def is_tgl(client: Client, message: Message) -> bool:
    # Check if the message includes the Telegram link
    try:
        # Bypass prepare
        gid = message.chat.id
        description = get_description(client, gid)
        pinned_message = get_pinned(client, gid)
        pinned_text = get_text(pinned_message)

        # Check links
        bypass = get_stripped_link(get_channel_link(message))
        links = get_links(message)
        tg_links = list(filter(lambda l: is_regex_text("tgl", l), links))
        bypass_list = [link for link in tg_links if (f"{bypass}/" in f"{link}/"
                                                     or link in description
                                                     or link in pinned_text)]
        if len(bypass_list) != len(tg_links):
            return True

        # Check text
        text = get_text(message)
        for bypass in bypass_list:
            text = text.replace(bypass, "")

        if is_regex_text("tgl", text):
            return True

        # Check mentions
        entities = message.entities or message.caption_entities
        if entities:
            for en in entities:
                if en.type == "mention":
                    username = get_entity_text(message, en)[1:]
                    if message.chat.username and username == message.chat.username:
                        continue

                    if username in description:
                        continue

                    if username in pinned_text:
                        continue

                    peer_type, peer_id = resolve_username(client, username)
                    if peer_type == "channel" and peer_id not in glovar.except_ids["channels"]:
                        return True

                    if peer_type == "user":
                        member = get_chat_member(client, message.chat.id, peer_id)
                        if member is False:
                            return True

                        if member and member.status not in {"creator", "administrator", "member", "restricted"}:
                            return True
    except Exception as e:
        logger.warning(f"Is tgl error: {e}", exc_info=True)

    return False


def is_watch_user(message: Message, the_type: str) -> bool:
    # Check if the message is sent by a watch user
    try:
        if message.from_user:
            uid = message.from_user.id
            now = get_now()
            until = glovar.watch_ids[the_type].get(uid, 0)
            if now < until:
                return True
    except Exception as e:
        logger.warning(f"Is watch user error: {e}", exc_info=True)

    return False
