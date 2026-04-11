import hashlib
import os

from settings import get_settings

import Utils
from worlds.Files import APProcedurePatch, APTokenMixin, APTokenTypes

from worlds.AutoWorld import World

SUMMER_FOREST_ELORA_WARP = 0x1057960
AUTUMN_PLAINS_ELORA_WARP = 0x24f6a20

class Spyro2ProcedurePatch(APProcedurePatch, APTokenMixin):
    game = "Spyro 2: Ripto's Rage"
    hash = ""
    # hash = ...
    patch_file_ending = ".apspyro2"
    result_file_ending = ".bin"

    @classmethod
    def get_source_data(cls) -> bytes:
        with open("Spyro 2.bin", "rb") as infile:
            base_rom_bytes = bytes(infile.read())

        return base_rom_bytes

def write_tokens(world: World, patch: Spyro2ProcedurePatch):
    patch.write_token(APTokenTypes.WRITE, SUMMER_FOREST_ELORA_WARP, int(0).to_bytes(4, 'little'))
    patch.write_token(APTokenTypes.WRITE, AUTUMN_PLAINS_ELORA_WARP, int(0).to_bytes(4, 'little'))
    patch.write_file("token_data.bin", patch.get_token_binary())

def get_base_rom_bytes(file_name: str = "") -> bytes:
    base_rom_bytes = getattr(get_base_rom_bytes, "base_rom_bytes", None)
    if not base_rom_bytes:
        file_name = get_base_rom_path(file_name)
        # Despite function name, seems to be generic
        base_rom_bytes = bytes(Utils.read_snes_rom(open(file_name, "rb"), False))

        #basemd5 = hashlib.md5()
        #basemd5.update(base_rom_bytes)
        #md5hash = basemd5.hexdigest()
        #if "d060cf67ca17c0ae07d9cbfc50a545d3" != md5hash:
        #    raise Exception(
        #        "Supplied Base Rom does not match known MD5 for"
        #        "Spyro: Attack of the Rhynocs (U) "
        #        "Get the correct game and version, then dump it"
        #    )
        get_base_rom_bytes.base_rom_bytes = base_rom_bytes
    return base_rom_bytes

def get_base_rom_path(file_name: str = "") -> str:
    if not file_name:
        file_name = get_settings().spyro2.rom_file
    if not os.path.exists(file_name):
        file_name = Utils.user_path(file_name)
    return file_name
