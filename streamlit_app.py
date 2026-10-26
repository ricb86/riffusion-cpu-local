"""
Interface local (Streamlit) para gerar música com Riffusion no CPU.

Uso:
    ./run.sh            # inicia e abre o navegador em http://127.0.0.1:8501
"""

from __future__ import annotations

import io
import os
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
import torch
from PIL import Image

from riffusion.datatypes import InferenceInput, PromptInput
from riffusion.riffusion_pipeline import RiffusionPipeline
from riffusion.spectrogram_image_converter import SpectrogramImageConverter
from riffusion.spectrogram_params import SpectrogramParams

REPO_DIR = Path(__file__).resolve().parent
CKPT_DIR = Path(
    os.environ.get("RIFFUSION_CKPT", str(Path.home() / "AI-Music/models/riffusion-model-v1"))
)
OUTPUT_DIR = Path(os.environ.get("RIFFUSION_OUTPUT", str(Path.home() / "AI-Music/outputs")))
SEED_DIR = REPO_DIR / "seed_images"

st.set_page_config(page_title="Riffusion Local", page_icon="🎵", layout="wide")


@st.cache_resource(show_spinner=False)
def load_pipeline() -> RiffusionPipeline:
    torch.set_num_threads(max(1, (os.cpu_count() or 4) // 2))
    return RiffusionPipeline.load_checkpoint(
        checkpoint=str(CKPT_DIR),
        use_traced_unet=False,
        dtype=torch.float32,
        device="cpu",
        low_cpu_mem_usage=True,
    )


@st.cache_resource(show_spinner=False)
def load_converter() -> SpectrogramImageConverter:
    return SpectrogramImageConverter(SpectrogramParams())


def seed_images() -> list[str]:
    names = sorted(p.stem for p in SEED_DIR.glob("*.png") if not p.name.startswith("mask_"))
    return names or ["og_beat"]


def generate(
    *,
    prompt_start: str,
    prompt_end: str,
    steps: int,
    guidance: float,
    denoising: float,
    seed: int,
    seed_image: str,
    init_image: Image.Image | None,
) -> tuple[Image.Image, object]:
    pipe = load_pipeline()
    converter = load_converter()

    params = SpectrogramParams()
    inputs = InferenceInput(
        start=PromptInput(
            prompt=prompt_start,
            seed=seed,
            denoising=denoising,
            guidance=guidance,
        ),
        end=PromptInput(
            prompt=prompt_end or prompt_start,
            seed=seed,
            denoising=denoising,
            guidance=guidance,
        ),
        alpha=0.5,
        num_inference_steps=steps,
        seed_image_id=seed_image,
    )

    if init_image is None:
        init_image = Image.open(SEED_DIR / f"{seed_image}.png").convert("RGB")
    else:
        init_image = init_image.convert("RGB").resize((512, 512), Image.LANCZOS)

    with torch.inference_mode():
        spec = pipe.riffuse(inputs, init_image=init_image)

    audio = converter.audio_from_spectrogram_image(spec)
    return spec, audio


def main() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stAppDeployButton"], [data-testid="stSkillsNudge"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("🎵 Riffusion Local")
    st.caption(
        "Geração de música por IA 100% local (CPU). "
        "Cada clipe tem ~5 segundos e leva cerca de 1 a 2 minutos."
    )

    if not CKPT_DIR.exists():
        st.error(
            f"Modelo não encontrado em `{CKPT_DIR}`.\n\n"
            "Baixe com o script `download_model.sh` ou defina a variável RIFFUSION_CKPT."
        )
        st.stop()

    with st.sidebar:
        st.header("Parâmetros")

        seed_image = st.selectbox(
            "Base rítmica (seed image)",
            seed_images(),
            index=seed_images().index("og_beat") if "og_beat" in seed_images() else 0,
            help="Cada base tem um 'groove' inicial diferente.",
        )
        steps = st.slider(
            "Passos de difusão",
            min_value=8,
            max_value=40,
            value=16,
            step=1,
            help="Mais passos = melhor qualidade, porém mais lento (~6 s por passo).",
        )
        guidance = st.slider("Guidance (adesão ao prompt)", 1.0, 15.0, 7.0, 0.5)
        denoising = st.slider(
            "Força de recriação",
            0.1,
            1.0,
            0.75,
            0.05,
            help="Baixo mantém a base; alto deixa o prompt mandar mais.",
        )
        seed = st.number_input("Seed", min_value=0, max_value=2_147_483_647, value=42, step=1)

        st.divider()
        ref = st.file_uploader(
            "Imagem de referência (opcional)",
            type=["png", "jpg", "jpeg"],
            help="Use um espectrograma para continuar/variação.",
        )
        use_last = st.checkbox("Usar o último espectrograma gerado como referência", value=False)

        st.divider()
        st.caption(
            f"Modelo: `{CKPT_DIR.name}`\n\n"
            f"Threads: {torch.get_num_threads()}\n\n"
            f"Saídas: `{OUTPUT_DIR}`"
        )

    col_prompt, col_preview = st.columns([3, 2])

    with col_prompt:
        prompt_start = st.text_area(
            "Prompt (o que você quer ouvir)",
            value="lofi hip hop beat, warm vinyl crackle, mellow piano, relaxed",
            height=90,
        )
        prompt_end = st.text_area(
            "Prompt final (opcional, para interpolar)",
            value="",
            height=70,
            placeholder="Deixe vazio para manter o mesmo estilo do início",
        )

    init_image = None
    last = st.session_state.get("last_spec")
    if use_last and last is not None:
        init_image = last
    elif ref is not None:
        init_image = Image.open(ref)

    with col_preview:
        if init_image is not None:
            st.image(init_image, caption="Imagem de referência", width="stretch")
        else:
            st.image(
                Image.open(SEED_DIR / f"{seed_image}.png").convert("RGB"),
                caption=f"Base: {seed_image}",
                width="stretch",
            )

    if st.button("🎧 Gerar música", type="primary", width="stretch"):
        if not prompt_start.strip():
            st.warning("Digite um prompt.")
            st.stop()

        t0 = time.time()
        with st.status("Gerando... isso leva 1–2 minutos no CPU.", expanded=True) as status:
            st.write(f"Difusão: {steps} passos × ~6 s ≈ {steps * 6 // 60}min {steps * 6 % 60}s")
            spec, audio = generate(
                prompt_start=prompt_start.strip(),
                prompt_end=prompt_end.strip(),
                steps=steps,
                guidance=guidance,
                denoising=denoising,
                seed=int(seed),
                seed_image=seed_image,
                init_image=init_image,
            )
            status.update(label=f"Pronto em {time.time() - t0:.0f}s", state="complete")

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        wav_path = OUTPUT_DIR / f"riffusion_{stamp}.wav"
        png_path = OUTPUT_DIR / f"riffusion_{stamp}.png"
        audio.export(wav_path, format="wav")
        spec.save(png_path)

        st.session_state["last_spec"] = spec
        st.session_state["last_audio"] = wav_path

        st.success(f"Salvo em `{wav_path}`")
        st.audio(str(wav_path), format="audio/wav")
        st.image(spec, caption="Espectrograma gerado", width="stretch")

        with open(wav_path, "rb") as f:
            st.download_button(
                "⬇️ Baixar WAV",
                data=f.read(),
                file_name=wav_path.name,
                mime="audio/wav",
                width="stretch",
            )

    last_audio = st.session_state.get("last_audio")
    if last_audio and Path(last_audio).exists():
        st.divider()
        st.subheader("Último resultado")
        st.audio(str(last_audio), format="audio/wav")


if __name__ == "__main__":
    main()
