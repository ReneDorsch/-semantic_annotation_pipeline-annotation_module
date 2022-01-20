
from typing import List
from .annotation_model import Annotation
import core.schemas.datamodel as io

class KnowledgeObject:
    IDCounter = 1

    def __init__(self, annotation: Annotation):
        self.annotations: List[Annotation] = self._get_annotations_from_annotation_object(annotation)
        self.knowObjID = KnowledgeObject.IDCounter
        self.labels: List[str] = [_.label for _ in self.annotations]
        self.category: str = annotation.category
        self.specificCategory: str = annotation.specificCategory
        self._labels_normalized: List[str] = [" ".join([word.normalized_form for word in annotation.words]) for annotation in self.annotations]
        KnowledgeObject.IDCounter += 1

    def to_io(self) -> io.KnowledgeObject:
        return io.KnowledgeObject(**{
            'id': self.knowObjID,
            'labels': [_ for _ in self.labels],
            'category': self.specificCategory,
            'annotation_ids': [_.annotationID for _ in self.annotations]
        })

    def saveAsDictSmall(self):
        return self.knowObjID

    def save_as_dict(self):
        res = {
           'id': self.knowObjID,
           'category': self.specificCategory,
           'labels': self.labels
               }
        return res

    def _get_annotations_from_annotation_object(self, annotation: Annotation) -> List[Annotation]:
        annos = [annotation]
        annos.extend(annotation.synonymical_annotations)
        [self._add_knowledge_object_to_annotation(anno) for anno in annos]
        return annos

    def _add_knowledge_object_to_annotation(self, annotation):
        annotation.knowledgeObject = self


    def add_annotation(self, annotation: Annotation) -> None:
        if annotation not in self.annotations:
            self.annotations.append(annotation)
            self._add_knowledge_object_to_annotation(annotation)
            self._set_labels()
        if len(annotation.synonymical_annotations) > 0:
            for synonymAnnotation in annotation.synonymical_annotations:
                if synonymAnnotation not in self.annotations:
                    self.annotations.append(synonymAnnotation)
                    self._add_knowledge_object_to_annotation(synonymAnnotation)
                    self._set_labels()

    def _set_labels(self):
        for annotation in self.annotations:
            normalized_label = " ".join([_.normalized_form for _ in annotation.words])
            if annotation.label not in self.labels:
                self.labels.append(annotation.label)
            if normalized_label not in self._labels_normalized:
                self._labels_normalized.append(normalized_label)
            for synonym in annotation.synonymical_annotations:
                normalized_label = " ".join([_.normalized_form for _ in synonym.words])
                if synonym.label not in self.labels:
                    self.labels.append(synonym.label)
                if normalized_label not in self._labels_normalized:
                    self._labels_normalized.append(normalized_label)
