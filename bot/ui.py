"""Показ экранов: одно «живое» сообщение с баннером, которое редактируется на месте."""
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardMarkup, InputMediaPhoto, Message

from . import banners

_file_ids: dict[str, str] = {}


def _media(name: str):
    return _file_ids.get(name) or FSInputFile(banners.path(name))


def _remember(name: str, msg: Message | bool):
    if isinstance(msg, Message) and msg.photo and name not in _file_ids:
        _file_ids[name] = msg.photo[-1].file_id


async def show(target: Message | CallbackQuery, banner: str, text: str, kb: InlineKeyboardMarkup):
    if isinstance(target, CallbackQuery):
        msg = target.message
        if msg and msg.photo:
            try:
                res = await msg.edit_media(InputMediaPhoto(media=_media(banner), caption=text, parse_mode="HTML"), reply_markup=kb)
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
    res = await target.answer_photo(_media(banner), caption=text, parse_mode="HTML", reply_markup=kb)
    _remember(banner, res)
