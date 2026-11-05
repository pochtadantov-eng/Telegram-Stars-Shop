"""Показ экранов: одно «живое» сообщение с баннером (картинка или GIF), которое редактируется на месте."""
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (CallbackQuery, FSInputFile, InlineKeyboardMarkup, InputMediaAnimation, InputMediaPhoto,
                           Message)

from . import banners

_file_ids: dict[str, str] = {}


def _media(name: str):
    return _file_ids.get(name) or FSInputFile(banners.path(name))


def _remember(name: str, msg):
    if name in _file_ids or not isinstance(msg, Message):
        return
    if msg.animation:
        _file_ids[name] = msg.animation.file_id
    elif msg.photo:
        _file_ids[name] = msg.photo[-1].file_id


def _input_media(name: str, text: str):
    cls = InputMediaAnimation if banners.is_animation(name) else InputMediaPhoto
    return cls(media=_media(name), caption=text, parse_mode="HTML")


async def show(target: Message | CallbackQuery, banner: str, text: str, kb: InlineKeyboardMarkup):
    if isinstance(target, CallbackQuery):
        msg = target.message
        if msg and (msg.photo or msg.animation or msg.video):
            try:
                res = await msg.edit_media(_input_media(banner, text), reply_markup=kb)
                _remember(banner, res)
            except TelegramBadRequest as e:
                if "not modified" not in str(e):
                    raise
            return
        if msg:
            try:
                await msg.delete()
            except TelegramBadRequest:
                pass
        target = msg
    send = target.answer_animation if banners.is_animation(banner) else target.answer_photo
    res = await send(_media(banner), caption=text, parse_mode="HTML", reply_markup=kb)
    _remember(banner, res)
