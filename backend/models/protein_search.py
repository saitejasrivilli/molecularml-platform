import numpy as np
import logging
from typing import Optional
import hashlib

logger = logging.getLogger(__name__)

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available — using numpy cosine similarity")

try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available — using mock embeddings")


PROTEIN_DB = [
    {"id": "P01308", "name": "Insulin", "organism": "Homo sapiens", "function": "Glucose metabolism regulator",
     "sequence": "MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKT"},
    {"id": "P00533", "name": "EGFR", "organism": "Homo sapiens", "function": "Epidermal growth factor receptor",
     "sequence": "MRPSGTAGAALLALLAALCPASRALEEKKVCQGTSNKLTQLGTFEDHFLSLQRMFNNCEVVLGNLEITYVQRNYDLSFLKTIQEVAGYVLIALNTVERIPLENLQIIRGNMYYENSYALAVLSNYDANKTGLKELPMRNLQEILHGAVRFSNNPALCNVESIQWRDIVSSDFLSNMSMDFQNHLGSCQKCDPSCPNGSCWGAGEENCQKLTKIICAQQCSGRCRGKSPSDCCHNQCAAGCTGPRESDCLVCRKFRDEATCKDTCPPLMLYNPTTYQMDVNPEGKYSFGATCVKKCPRNYVVTDHGSCVRACGADSYEMEEDGVRKCKKCEGPCRKVCNGIGIGEFKDSLSINATNIKHFKNCTSISGDLHILPVAFRGDSFTHTPPLDPQELDILKTVKEITGFLLIQAWPENRTDLHAFENLEIIRGRTKQHGQFSLAVVSLNITSLGLRSLKEISDGDVIISGNKNLCYANTINWKKLFGTSGQKTKIISNRGENSCKATGQVCHALCSPEGCWGPEPRDCVSCRNVSRGRECVDKCNLLEGEPREFVENSECIQCHPECLPQAMNITCTGRGPDNCIQCAHYIDGPHCVKTCPAGVMGENNTLVWKYADAGHVCHLCHPNCTYGCTGPGLEGCPTNGPKIPSIATGMVGALLLLLVVALGIGLFMRRRHIVRKRTLRRLLQERELVEPLTPSGEAPNQALLRILKETEFKKIKVLGSGAFGTVYKGLWIPEGEKVKIPVAIKELREATSPKANKEILDEAYVMASVDNPHVCRLLGICLTSTVQLITQLMPFGCLLDYVREHKDNIGSQYLLNWCVQIAKGMNYLEDRRLVHRDLAARNVLVKTPQHVKITDFGLAKLLGAEEKEYHAEGGKVPIKWMALESILHRIYTHQSDVWSYGVTVWELMTFGSKPYDGIPASEISSILEKGERLPQPPICTIDVYMIMVKCWMIDADSRPKFRELIIEFSKMARDPQRYLVIQGDERMHLPSPTDSNFYRALMDEEDMDDVVDADEYLIPQQGFFSSPSTSRTPLLSSLSATSNNSTVACIDRNGLQSCPIKEDSFLQRYSSDPTGALTEDSIDDTFLPVPEYINQSVPKRPAGSVQNPVYHNQPLNPAPSRDPHYQDPHSTAVGNPEYLNTVQPTCVNSTFDSPAHWAQKGSHQISLDNPDYQQDFFPKEAKPNGIFKGSTAENAEYLRVAPQSSEFIGA"},
    {"id": "P68871", "name": "Hemoglobin subunit beta", "organism": "Homo sapiens", "function": "Oxygen transport",
     "sequence": "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"},
    {"id": "P00441", "name": "Superoxide dismutase", "organism": "Homo sapiens", "function": "Antioxidant defense",
     "sequence": "MATKAVCVLKGDGPVQGIINFEQKESNGPVKVWGSIKGLTEGLHGFHVHEFGDNTAGCTSAGPHFNPLSRKHGGPKDEERHVGDLGNVTADKDGVADVSIEDSVISLSGDHCIIGRTLVVHEKADDLGKGGNEESTKTGNAGSRLACGVIGIAQ"},
    {"id": "P04637", "name": "Tumor protein p53", "organism": "Homo sapiens", "function": "Tumor suppressor",
     "sequence": "MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGPDEAPRMPEAAPPVAPAPAAPTPAAPAPAPSWPLSSSVPSQKTYPQGLNGTVNLFRNLNQARRVEDAIQSQLSAEELGKADEATQNLITQHGQDIGMQLHQVVQAIEDRLNSVRNKFQPDTANQQLAKSIRGTRAQHTAASAESSIRMAELKEQRRNMHIGRQKGKNEKQRRNMHIQRQKGGKNEKGKNEKQRRNMHIQRQ"},
    {"id": "P0DTD1", "name": "SARS-CoV-2 Spike protein", "organism": "SARS-CoV-2", "function": "Viral entry",
     "sequence": "MFVFLVLLPLVSSQCVNLTTRTQLPPAYTNSFTRGVYYPDKVFRSSVLHSTQDLFLPFFSNVTWFHAIHVSGTNGTKRFDNPVLPFNDGVYFASTEKSNIIRGWIFGTTLDSKTQSLLIVNNATNVVIKVCEFQFCNDPFLGVYYHKNNKSWMESEFRVYSSANNCTFEYVSQPFLMDLEGKQGNFKNLREFVFKNIDGYFKIYSKHTPINLVRDLPQGFSALEPLVDLPIGINITRFQTLLALHRSYLTPGDSSSGWTAGAAAYYVGYLQPRTFLLKYNENGTITDAVDCALDPLSETKCTLKSFTVEKGIYQTSNFRVQPTESIVRFPNITNLCPFGEVFNATRFASVYAWNRKRISNCVADYSVLYNSASFSTFKCYGVSPTKLNDLCFTNVYADSFVIRGDEVRQIAPGQTGKIADYNYKLPDDFTGCVIAWNSNNLDSKVGGNYNYLYRLFRKSNLKPFERDISTEIYQAGSTPCNGVEGFNCYFPLQSYGFQPTNGVGYQPYRVVVLSFELLHAPATVCGPKKSTNLVKNKCVNFNFNGLTGTGVLTESNKKFLPFQQFGRDIADTTDAVRDPQTLEILDITPCSFGGVSVITPGTNTSNQVAVLYQDVNCTEVPVAIHADQLTPTWRVYSTGSNVFQTRAGCLIGAEHVNNSYECDIPIGAGICASYQTQTNSPRRARSVASQSIIAYTMSLGAENSVAYSNNSIAIPTNFTISVTTEILPVSMTKTSVDCTMYICGDSTECSNLLLQYGSFCTQLNRALTGIAVEQDKNTQEVFAQVKQIYKTPPIKDFGGFNFSQILPDPSKPSKRSFIEDLLFNKVTLADAGFIKQYGDCLGDIAARDLICAQKFNGLTVLPPLLTDEMIAQYTSALLAGTITSGWTFGAGAALQIPFAMQMAYRFNGIGVTQNVLYENQKLIANQFNSAIGKIQDSLSSTASALGKLQDVVNQNAQALNTLVKQLSSNFGAISSVLNDILSRLDKVEAEVQIDRLITGRLQSLQTYVTQQLIRAAEIRASANLAATKMSECVLGQSKRVDFCGKGYHLMSFPQSAPHGVVFLHVTYVPAQEKNFTTAPAICHDGKAHFPREGVFVSNGTHWFVTQRNFYEPQIITTDNTFVSGNCDVVIGIVNNTVYDPLQPELDSFKEELDKYFKNHTSPDVDLGDISGINASVVNIQKEIDRLNEVAKNLNESLIDLQELGKYEQYIKWPWYIWLGFIAGLIAIVMVTIMLCCMTSCCSCLKGCCSCGSCCKFDEDDSEPVLKGVKLHYT"},
    {"id": "P00760", "name": "Trypsin", "organism": "Bos taurus", "function": "Serine protease / digestion",
     "sequence": "MKTFIFLALLGAAVAFPVDDDDKIVGGYTCGANTVPYQVSLNSGYHFCGGSLINSQWVVSAAHCYKSGIQVRLGEDNINVVEGNEQFISASKSIVHPSYNSNTLNNDIMLIKLKSAALAANPVDDDDKIVGGYTCGANTVPYQ"},
    {"id": "P69905", "name": "Hemoglobin subunit alpha", "organism": "Homo sapiens", "function": "Oxygen transport",
     "sequence": "MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSHGSAQVKGHGKKVADALTNAVAHVDDMPNALSALSDLHAHKLRVDPVNFKLLSHCLLVTLAAHLPAEFTPAVHASLDKFLASVSTVLTSKYR"},
]


class ProteinSearch:
    def __init__(self):
        self._loaded = False
        self._index = None
        self._embeddings = None
        self._tokenizer = None
        self._model = None
        self._load()

    def _load(self):
        try:
            if TRANSFORMERS_AVAILABLE:
                logger.info("Loading ESM tokenizer...")
                self._tokenizer = AutoTokenizer.from_pretrained("facebook/esm2_t6_8M_UR50D")
                self._model = AutoModel.from_pretrained("facebook/esm2_t6_8M_UR50D")
                self._model.eval()
                logger.info("ESM model loaded")
            self._build_index()
            self._loaded = True
        except Exception as e:
            logger.error(f"Protein search load error: {e}")
            self._use_mock = True
            self._build_mock_index()
            self._loaded = True

    def _embed_sequence(self, sequence: str) -> np.ndarray:
        if not TRANSFORMERS_AVAILABLE or self._tokenizer is None:
            return self._mock_embed(sequence)
        try:
            import torch
            inputs = self._tokenizer(
                sequence[:512],
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            with torch.no_grad():
                outputs = self._model(**inputs)
            embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            norm = np.linalg.norm(embedding)
            return (embedding / norm).astype(np.float32)
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return self._mock_embed(sequence)

    def _mock_embed(self, sequence: str) -> np.ndarray:
        seed = int(hashlib.md5(sequence[:50].encode()).hexdigest(), 16) % (2**31)
        rng = np.random.RandomState(seed)
        vec = rng.randn(320).astype(np.float32)
        return vec / np.linalg.norm(vec)

    def _build_index(self):
        logger.info("Building FAISS protein index...")
        embeddings = []
        for protein in PROTEIN_DB:
            emb = self._embed_sequence(protein["sequence"])
            embeddings.append(emb)
        self._embeddings = np.stack(embeddings)
        dim = self._embeddings.shape[1]
        if FAISS_AVAILABLE:
            self._index = faiss.IndexFlatIP(dim)
            self._index.add(self._embeddings)
        logger.info(f"Index built with {len(PROTEIN_DB)} proteins, dim={dim}")

    def _build_mock_index(self):
        embeddings = []
        for protein in PROTEIN_DB:
            emb = self._mock_embed(protein["sequence"])
            embeddings.append(emb)
        self._embeddings = np.stack(embeddings)

    def _cosine_similarity(self, query: np.ndarray, top_k: int) -> tuple:
        sims = self._embeddings @ query
        indices = np.argsort(sims)[::-1][:top_k]
        return sims[indices], indices

    def is_loaded(self):
        return self._loaded

    def search(self, sequence: str, top_k: int = 5) -> list:
        if len(sequence) < 10:
            raise ValueError("Sequence too short — minimum 10 amino acids required")
        query_emb = self._embed_sequence(sequence)
        top_k = min(top_k, len(PROTEIN_DB))
        if FAISS_AVAILABLE and self._index is not None:
            scores, indices = self._index.search(query_emb.reshape(1, -1), top_k)
            scores, indices = scores[0], indices[0]
        else:
            scores, indices = self._cosine_similarity(query_emb, top_k)
        results = []
        for score, idx in zip(scores, indices):
            protein = PROTEIN_DB[idx]
            results.append({
                "rank": len(results) + 1,
                "uniprot_id": protein["id"],
                "name": protein["name"],
                "organism": protein["organism"],
                "function": protein["function"],
                "similarity_score": round(float(score), 4),
                "sequence_preview": protein["sequence"][:60] + "...",
            })
        return results
