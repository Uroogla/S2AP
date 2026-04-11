using Serilog;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace S2AP.Patching
{

    public class PatchChange
    {
        public uint romAddress { get; set; }
        public byte[] oldBytes { get; set; }
        public byte[] newBytes { get; set; }

        public PatchChange(uint romAddress, byte[] oldBytes, byte[] newBytes)
        {
            this.romAddress = romAddress;
            this.oldBytes = oldBytes;
            this.newBytes = newBytes;
        }
    }

    public class Patcher
    {
        public static bool WriteCue(string baseCuePath, string outputPath, string newRomPath)
        {
            try
            {
                File.Copy(baseCuePath, outputPath, true);
                string[] arrLine = File.ReadAllLines(outputPath);
                arrLine[0] = $"FILE \"{newRomPath}\" BINARY";
                File.WriteAllLines(outputPath, arrLine);
            }
            catch (FileNotFoundException)
            {
                Log.Logger.Error("Could not find cue to patch.");
                return false;
            }
            catch (DirectoryNotFoundException)
            {
                Log.Logger.Error("Could not find cue to patch.");
                return false;
            }
            catch (Exception e)
            {
                Log.Logger.Error("Error patching cue\r\n" + e.ToString());
                return false;
            }
            return true;
        }

        private static bool validateRomBlock(BinaryReader reader, uint romAddress, int readLength, byte[] comparison)
        {
            if (readLength > comparison.Length)
            {
                Log.Logger.Error("Patching process failed due to an error in the S2AP executable.");
                return false;
            }
            byte[] bytesRom = ReadDataBlock(reader, romAddress, readLength);
            for (int i = 0; i < readLength; i++)
            {
                if (comparison[i] != bytesRom[i])
                {
                    Log.Logger.Error("Your base ROM does not appear to be compatible\r\n" +
                        "with the patch. It may already be patched or otherwise modded.");
                    return false;
                }
            }
            return true;
        }
        public static bool WriteRom(string baseRomPath, string outputPath)
        {
            List<PatchChange> changes = new List<PatchChange>()
            {
                new PatchChange(Addresses.RomSFEloraWarp, Addresses.EloraWarpCode, [0, 0, 0, 0]),       // Remove SF Elora Warp
                new PatchChange(Addresses.RomAPEloraWarp, Addresses.EloraWarpCode, [0, 0, 0, 0]),       // Remove AP Elora Warp
                new PatchChange(Addresses.RomDialogueOrbCount, Addresses.OrbCountCode, [0, 0, 0, 0]),   // Remove orb increase during dialogue
                new PatchChange(Addresses.RomLoadOrbCount, Addresses.OrbCountCode, [0, 0, 0, 0]),       // Remove setting orb count on loading save
                // This code is in every non-boss level overlay, but only the homeworlds have freestanding orbs.
                // If we needed to support a mod that adds them, more changes would be needed.
                new PatchChange(Addresses.RomSFOrbCount, Addresses.OrbCountCode, [0, 0, 0, 0]),         // Remove orb increase on loose SF orbs
                new PatchChange(Addresses.RomAPOrbCount, Addresses.OrbCountCode, [0, 0, 0, 0]),         // Remove orb increase on loose AP orbs
                new PatchChange(Addresses.RomWTOrbCount, Addresses.OrbCountCode, [0, 0, 0, 0]),         // Remove orb increase on loose WT orbs
                new PatchChange(Addresses.RomPlayBeep, Addresses.PlayBeepCode, [0, 0, 0, 0]),           // Remove gem count desync beep sound
            };
            try
            {
                // Validate source rom
                using (var reader = new BinaryReader(File.OpenRead(baseRomPath)))
                {
                    foreach (PatchChange change in changes)
                    {
                        if (!validateRomBlock(reader, change.romAddress, change.newBytes.Length, change.oldBytes))
                        {
                            return false;
                        }
                    }
                }
                File.Copy(baseRomPath, outputPath, true);
                using (var writer = new BinaryWriter(File.OpenWrite(outputPath)))
                {
                    foreach (PatchChange change in changes)
                    {
                        WriteDataBlock(writer, change.newBytes, change.romAddress);
                    }
                }
            }
            catch (FileNotFoundException)
            {
                Log.Logger.Error("Could not find ROM to patch.");
                return false;
            }
            catch (DirectoryNotFoundException)
            {
                Log.Logger.Error("Could not find ROM to patch.");
                return false;
            }
            catch (Exception e)
            {
                Log.Logger.Error("Error patching ROM\r\n" + e.ToString());
                return false;
            }
            return true;
        }
        private static byte[] ReadDataBlock(BinaryReader reader, long blockStartAddress, int blockSize)
        {
            reader.BaseStream.Seek(blockStartAddress, SeekOrigin.Begin);
            byte[] item = reader.ReadBytes(blockSize);

            return item;
        }

        private static void WriteDataBlock(BinaryWriter writer, byte[] obj, long startAddress)
        {
            writer.BaseStream.Seek(startAddress, SeekOrigin.Begin);
            writer.Write(obj);
        }
    }
}
