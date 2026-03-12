import discord
import requests
import subprocess
import tempfile
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


def escape_lua(code):
    # تهرب الأحرف الخاصة
    code = code.replace("\\", "\\\\")
    code = code.replace('"', '\\"')
    code = code.replace("\n", "\\n")
    return code


@client.event
async def on_ready():
    print(f"Bot running as {client.user}")


@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith("!run"):
        args = message.content.split()

        if len(args) < 2:
            await message.channel.send("استخدم: `!run الرابط`")
            return

        url = args[1]

        await message.channel.send("جاري تحميل الكود...")

        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                await message.channel.send("فشل تحميل الرابط")
                return

            code = r.text
            escaped = escape_lua(code)

            # Lua sandbox + load + pcall للتعامل مع return و print
            lua_script = f'''
local f, err = load("{escaped}")
if not f then
    print(err)
else
    local status, result = pcall(f)
    if not status then
        print(result)
    elseif result ~= nil then
        print(result)
    end
end
'''

            # حفظ السكربت مؤقتًا
            with tempfile.NamedTemporaryFile(delete=False, suffix=".lua") as f:
                f.write(lua_script.encode())
                path = f.name

            # تشغيل Lua
            result = subprocess.run(
                ["lua", path],
                capture_output=True,
                text=True,
                timeout=10
            )

            output = result.stdout or result.stderr
            if not output:
                output = "لا يوجد ناتج"

            # الحد الأقصى للرسالة في Discord
            if len(output) > 1900:
                output = output[:1900] + "\n...تم القطع"

            await message.channel.send(f"```{output}```")

        except Exception as e:
            await message.channel.send(f"حدث خطأ:\n{e}")


client.run(TOKEN)
