from ._base_api_ import TransformationStrategy
from ..annotation_model import DocumentAnalysis
from ..datamodels.annotation_model import Annotation
from ..datamodels.knowledge_object_model import KnowledgeObject
import copy
from typing import List
import regex
from fuzzywuzzy import process, fuzz
from core.config import FUZZY_WUZZY_COMPARISON_SCORE



class KnowledgeObjectStrategy(TransformationStrategy):

    def preprocess_data(self, data: DocumentAnalysis) -> None:
        pass

    def postprocess_data(self, data: DocumentAnalysis) -> None:
        pass

    def process_data(self, data: DocumentAnalysis) -> None:

        def helper_function():
            res = []
            words = []
            annotations = data.annotations
            for annotation in annotations:
                already_annotated = False
                for word in annotation.words:
                    if word in words:
                        already_annotated = True
                if already_annotated:
                    continue
                words.extend(annotation.words)
                res.append(annotation)
            return res

        annotations = helper_function()
        zwerg = copy.copy(annotations)

        # self.adjustCategories(annotations)
        kObjs = self.set_knowledgeObjects_for_text(zwerg)

        data.knowledgeObjects = kObjs
        kObjs = self.set_knowledgeObjects_for_tables(data)

    def set_knowledgeObjects_for_text(self, annotations: List[Annotation]) -> List[KnowledgeObject]:
        """ Identifies the knowledge Objects for the text. And returns them. """
        res = []
        while annotations:
            annotation: Annotation = annotations.pop(0)
            annotation.adjustInformation()
            knowObj = KnowledgeObject(annotation)
            listOfAnnotationToRemove = self._add_annotations_to_kObj(knowObj, annotations)

            annotation.adjustInformation()
            annotations = [_ for _ in annotations if _ not in listOfAnnotationToRemove]
            res.append(knowObj)
        return res

    def _add_annotations_to_kObj(self, kObj: KnowledgeObject, annotations: List[Annotation]) -> List[Annotation]:
        ''' Adds other annotation to the found Annotation if these are similiar enough. '''
        annotations_to_delete = []
        while True:
            counter = 0
            for annotation in annotations:
                if self._annotation_is_part_of_kObj(kObj, annotation):
                    kObj.add_annotation(annotation)
                    annotations_to_delete.append(annotation)
                    annotations.remove(annotation)
                    counter += 1

            if counter == 0:
                break

        return annotations_to_delete

    def set_knowledgeObjects_for_tables(self, data) -> List[KnowledgeObject]:
        res = []
        for table in data.tables:
            res.extend(table.annotate_cells())
        return res


    def _annotation_is_part_of_kObj(self, kObj: KnowledgeObject, annotation: Annotation) -> bool:
        ''' Checks if the annotation is part of a knowledge Object '''
        contains_number: bool = self._has_numeric_value(annotation)
        is_small: bool = len(annotation.label.replace(" ","")) < 4
        if contains_number or is_small:
            return self._is_part_of_knowledgeObject_exact(kObj, annotation)
        else:
            return self._is_part_of_knowledgeObject_fuzzy(kObj, annotation)
        return False


    def _has_numeric_value(self, annotation: Annotation) -> bool:
        ''' Some Rules to check if the string is a number '''
        regexDigit = ' \d+(,\d+|) '
        words_in_label = [word.normalized_form for word in annotation.words]
        # If a single Word is a Number
        for word in words_in_label:
            if regex.search(regexDigit, " " + word + " "):
                return True
        return False


    def _is_part_of_knowledgeObject_exact(self, kObj: KnowledgeObject, annotation: Annotation) -> bool:
        ''' Checks that an annotation is part of an Knowledge Object by exact comparison. '''

        normalized_labels = [_.replace(" ", "") for _ in kObj._labels_normalized]
        normalized_annotation = "".join(word.normalized_form for word in annotation.words)
        is_normalized: bool = normalized_annotation in normalized_labels

        simplified_labels = [_.replace(" ", "").lower() for _ in kObj.labels]
        simplified_annotation = "".join(word.word.lower() for word in annotation.words)
        is_simplified: bool = simplified_annotation in simplified_labels

        if is_simplified or is_normalized:
            return True

        for synonymAnnotation in annotation.synonymical_annotations:
            normalized_annotation = "".join(word.normalized_form for word in synonymAnnotation.words)
            simplified_annotation = "".join(word.word.lower() for word in annotation.words)

            is_simplified: bool = simplified_annotation in simplified_labels
            is_normalized: bool = normalized_annotation in normalized_labels

            if is_simplified or is_normalized:
                return True
        return False


    def _is_part_of_knowledgeObject_fuzzy(self, kObj: KnowledgeObject, annotation: Annotation) -> bool:
        ''' Checks that an annotation is part of an Knowledge Object by fuzzy comparison. '''
        normalized_kObj_labels = [_.lower() for _ in kObj._labels_normalized]
        normalized_word = " ".join([word.normalized_form for word in annotation.words])
        results = process.extract(normalized_word, normalized_kObj_labels, scorer=fuzz.token_set_ratio)

        highestConfidenceOfResult = results[0][1]
        if highestConfidenceOfResult >= FUZZY_WUZZY_COMPARISON_SCORE:
            return True
        if len(annotation.synonymical_annotations) > 0:
            for synonymAnnotation in annotation.synonymical_annotations:
                normalized_synonym = " ".join([word.normalized_form for word in synonymAnnotation.words])
                results = process.extract(normalized_synonym, normalized_kObj_labels, scorer=fuzz.token_set_ratio)
                highestConfidenceOfResult = results[0][1]
                if highestConfidenceOfResult >= FUZZY_WUZZY_COMPARISON_SCORE:
                    return True
        return False
