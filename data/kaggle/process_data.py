import pathlib

import pandas as pd
import spacy


def lemmatize(doc):
    def validate(token):
        allowed = ["VERB", "NOUN", "PROPN", "ADJ", "SCONJ"]
        return token.pos_ in allowed and not token.is_stop and not token.is_digit and not token.is_bracket and not token.is_punct

    return set((token.lemma_.lower() for token in filter(validate, doc)))


def extract_keywords(questions, nlp=None):
    if nlp is None:
        nlp = spacy.load("en_core_web_trf")

    return [lemmatize(doc) for doc in nlp.pipe(questions, batch_size=400)]


def build_universum(lemmatized_data):
    universum = []

    for r in lemmatized_data:
        universum.extend(r)
    
    return sorted(set(universum))


def build_context(df, lemmatized_data):
    universum = build_universum(lemmatized_data)

    context = pd.DataFrame(index=df.index, columns=universum)

    for idx, r in enumerate(lemmatized_data):
        context.loc[idx] = [lemma in r for lemma in universum]
    
    context.index = df["Questions"]

    return context


if __name__ == "__main__":
    df = pd.read_csv(pathlib.Path.cwd() / "data" / "kaggle" / "kaggle.csv")

    lemmatized_data = extract_keywords(df["Questions"])

    context = build_context(df, lemmatized_data)

    context.to_csv(pathlib.Path.cwd() / "data" / "kaggle" / "kaggle_context.csv")

