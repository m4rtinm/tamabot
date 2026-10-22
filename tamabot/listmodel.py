from PySide6.QtCore import QAbstractListModel, QByteArray, QModelIndex, Qt, Property, Signal


class DictListModel(QAbstractListModel):
    """Lista de dicts para QML que se actualiza con diffs (mantiene delegados y animaciones)."""

    countChanged = Signal()

    def __init__(self, key, roles, parent=None):
        super().__init__(parent)
        self._key = key
        self._items = []
        self._roles = {Qt.ItemDataRole.UserRole + 1 + i: name for i, name in enumerate(roles)}

    def roleNames(self):
        return {rid: QByteArray(name.encode()) for rid, name in self._roles.items()}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._items)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._items):
            return None
        name = self._roles.get(role)
        return self._items[index.row()].get(name) if name else None

    def items(self):
        return list(self._items)

    def sync(self, items):
        before = len(self._items)
        wanted = {it[self._key] for it in items}
        for row in reversed(range(len(self._items))):
            if self._items[row][self._key] not in wanted:
                self.beginRemoveRows(QModelIndex(), row, row)
                del self._items[row]
                self.endRemoveRows()
        for target, item in enumerate(items):
            cur = next((r for r, it in enumerate(self._items) if it[self._key] == item[self._key]), None)
            if cur is None:
                self.beginInsertRows(QModelIndex(), target, target)
                self._items.insert(target, dict(item))
                self.endInsertRows()
                continue
            if cur != target:  # cur > target siempre: lo anterior ya esta ordenado
                self.beginMoveRows(QModelIndex(), cur, cur, QModelIndex(), target)
                self._items.insert(target, self._items.pop(cur))
                self.endMoveRows()
            if self._items[target] != item:
                self._items[target] = dict(item)
                idx = self.index(target)
                self.dataChanged.emit(idx, idx)
        if len(self._items) != before:
            self.countChanged.emit()

    count = Property(int, lambda self: len(self._items), notify=countChanged)
