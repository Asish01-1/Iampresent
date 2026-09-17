import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModel


class DinoV2:

    def __init__(self):

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.processor = AutoImageProcessor.from_pretrained(
            "facebook/dinov2-small"
        )

        self.model = AutoModel.from_pretrained(
            "facebook/dinov2-small"
        )

        self.model.to(self.device)
        self.model.eval()

        print("DINOv2 device:", self.device)

    def extract(self, image):

        if not isinstance(image, Image.Image):
            image = Image.fromarray(image)

        inputs = self.processor(
            images=image,
            return_tensors="pt"
        )

        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
        }

        with torch.no_grad():

            outputs = self.model(**inputs)

        embedding = outputs.last_hidden_state[:, 0]

        embedding = torch.nn.functional.normalize(
            embedding,
            p=2,
            dim=1
        )

        return embedding.cpu().numpy()[0]