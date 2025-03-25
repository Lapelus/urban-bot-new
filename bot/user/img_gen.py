import PIL.Image
from io import BytesIO

from PIL import ImageFont, ImageDraw


async def ticket_gen(ticket_id, price):
    draft = PIL.Image.open(r'C:\Users\User\PycharmProjects\urban_bot\bot\ticket_draft.jpeg')
    font_id = ImageFont.truetype("InriaSerif-Regular.ttf",96)
    font_price = ImageFont.truetype("helvetica_bold.otf",40)
    draw = ImageDraw.Draw(draft)
    price_position = (132, 609)
    id_position = (177, 263)

    text_color = (51, 53, 42)

    draw.text(id_position, text=f"{ticket_id}", fill=text_color, font=font_id)
    draw.text(price_position, text=f"{price}", fill=text_color, font=font_price)

    output = BytesIO()
    draft.save(output, format="PNG")
    output.seek(0)

    return output.read()





