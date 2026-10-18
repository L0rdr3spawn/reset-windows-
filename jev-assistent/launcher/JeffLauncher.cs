// JeffLauncher.cs - kleiner Starter für den Sprachassistenten (wird zu Jeff.exe).
//
// Warum: Im Windows-Autostart stand bisher "pythonw" (Python Software Foundation) - nicht
// als Jeff erkennbar. Jeff.exe trägt Namen und Herausgeber in den Dateieigenschaften,
// startet pythonw.exe mit jev_assistent.py unsichtbar und beendet sich sofort wieder.
//
// Übersetzt wird von autostart.py (python autostart.py ein) mit dem csc.exe aus .NET 4,
// zusammen mit der dort erzeugten Versionsinfo.cs (Name aus config.json).
// Nur C# 5 - der csc.exe von Windows kann nichts Neueres.
using System;
using System.Diagnostics;
using System.IO;
using System.Security.AccessControl;
using System.Threading;
using System.Windows.Forms;

static class JeffLauncher
{
    // Muss zu MUTEX_NAME in jev_assistent.py passen (dort ist die eigentliche Sperre)
    const string MUTEX_NAME = "Local\\JevAssistent";

    [STAThread]
    static int Main()
    {
        string ordner = AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\');
        string skript = Path.Combine(ordner, "jev_assistent.py");

        // Läuft schon? Dann gar nicht erst Python laden (jev_assistent.py prüft es sonst selbst)
        Mutex m;
        if (Mutex.TryOpenExisting(MUTEX_NAME, MutexRights.Synchronize, out m))
        {
            m.Dispose();
            return 0;
        }

        if (!File.Exists(skript))
            return Fehler("jev_assistent.py nicht gefunden in\n" + ordner);
        string pythonw = PythonwFinden();
        if (pythonw == null)
            return Fehler("pythonw.exe nicht gefunden (erwartet unter\n"
                          + Environment.GetEnvironmentVariable("LOCALAPPDATA") + "\\Programs\\Python\\Python312).");

        var info = new ProcessStartInfo(pythonw, "\"" + skript + "\"");
        info.WorkingDirectory = ordner;
        info.UseShellExecute = false;
        info.CreateNoWindow = true;
        info.WindowStyle = ProcessWindowStyle.Hidden;
        try
        {
            Process.Start(info).Dispose();
        }
        catch (Exception e)
        {
            return Fehler("Jeff konnte nicht gestartet werden:\n" + e.Message);
        }
        return 0;
    }

    static string PythonwFinden()
    {
        string lokal = Environment.GetEnvironmentVariable("LOCALAPPDATA");
        if (!String.IsNullOrEmpty(lokal))
        {
            string p = Path.Combine(lokal, @"Programs\Python\Python312\pythonw.exe");
            if (File.Exists(p))
                return p;
        }
        // Sonst neben dem python.exe aus PATH (nicht der Store-Platzhalter in WindowsApps)
        string pfad = Environment.GetEnvironmentVariable("PATH") ?? "";
        foreach (string roh in pfad.Split(';'))
        {
            string dir = roh.Trim().Trim('"');
            if (dir.Length == 0 || dir.IndexOf("WindowsApps", StringComparison.OrdinalIgnoreCase) >= 0)
                continue;
            try
            {
                if (File.Exists(Path.Combine(dir, "python.exe")) && File.Exists(Path.Combine(dir, "pythonw.exe")))
                    return Path.Combine(dir, "pythonw.exe");
            }
            catch (ArgumentException)
            {
                // ungültiger Eintrag in PATH
            }
        }
        return null;
    }

    static int Fehler(string text)
    {
        MessageBox.Show(text, "Sprachassistent", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        return 1;
    }
}
