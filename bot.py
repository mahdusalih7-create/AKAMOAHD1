import discord
import requests
import subprocess
import tempfile
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)


def escape_lua(code):
    code = code.replace("\\", "\\\\")
    code = code.replace('"', '\\"')
    code = code.replace("\n", "\\n")
    return code


@client.event
async def on_ready():
    print(f"Bot running: {client.user}")


@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith("!run"):
        args = message.content.split(" ")

        if len(args) < 2:
            await message.channel.send("استخدم: !run الرابط")
            return

        url = args[1]

        try:
            r = requests.get(url)

            if r.status_code != 200:
                await message.channel.send("فشل تحميل الرابط")
                return

            code = r.text
            escaped = escape_lua(code)

            lua_script = f'''
print(loadstring("{escaped}")())
'''

            with tempfile.NamedTemporaryFile(delete=False, suffix=".lua") as f:
                f.write(lua_script.encode())
                path = f.name

            result = subprocess.run(
                ["lua", path],
                capture_output=True,
                text=True,
                timeout=10
            )

            output = result.stdout or result.stderr

            if not output:
                output = "لا يوجد ناتج"

            if len(output) > 1900:
                output = output[:1900]

            await message.channel.send(f"```{output}```")

        except Exception:
            await message.channel.send("صار خطأ أثناء تشغيل الكود")


client.run(TOKEN)
