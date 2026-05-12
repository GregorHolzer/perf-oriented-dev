#include "linked_list.hpp"
#include <numeric>
#include <stdexcept>
#include <vector>

template<class T>
LinkedList<T>::iterator::iterator(LinkedListNode<T>* ptr)
  : ptr(ptr)
{
}

template<class T>
T&
LinkedList<T>::iterator::operator*()
{
  return ptr->value;
}

template<class T>
LinkedList<T>::iterator&
LinkedList<T>::iterator::operator++()
{
  ptr = ptr->next;
  return *this;
}

template<class T>
bool
LinkedList<T>::iterator::operator!=(const iterator& other)
{
  return this->ptr != other.ptr;
}

template<class T>
LinkedList<T>::iterator
LinkedList<T>::begin()
{
  return iterator(before_start_node.next);
}

template<class T>
LinkedList<T>::iterator
LinkedList<T>::before_begin()
{
  return iterator(&before_start_node);
}

template<class T>
LinkedList<T>::iterator
LinkedList<T>::end()
{
  return iterator(nullptr);
}

template<class T>
LinkedList<T>::iterator
LinkedList<T>::insert_after(iterator pos, const T& value)
{
  auto node = pos.ptr;
  auto new_node = new LinkedListNode<T>();
  new_node->value = value;
  new_node->next = node->next;
  node->next = new_node;
  ++_size;
  return iterator(new_node);
}

template<class T>
LinkedList<T>::iterator
LinkedList<T>::erase_after(iterator pos)
{
  auto node = pos.ptr;
  auto node_to_delete = node->next;
  if (node_to_delete == nullptr)
    return this->end();
  node->next = node_to_delete->next;
  delete node_to_delete;
  --_size;
  return iterator(node->next);
}

template<class T>
size_t
LinkedList<T>::size()
{
  return _size;
}

template<class T>
LinkedList<T>::~LinkedList()
{
  auto node = before_start_node.next;
  while (node != nullptr) {
    auto next = node->next;
    delete node;
    node = next;
  }
}

template<class T>
void
LinkedList<T>::shuffle_list(int seed)
{
  if (_size == 0)
    return;

  srand(seed);
  auto vec = std::vector<int>(_size);
  auto nodes = std::vector<LinkedListNode<T>*>(_size);
  auto current_node = before_start_node.next;
  size_t idx = 0;
  while (current_node != nullptr) {
    nodes[idx] = current_node;
    current_node = current_node->next;
    ++idx;
  }
  std::iota(vec.begin(), vec.end(), 0);
  for (size_t i = vec.size() - 1; i > 0; --i) {
    size_t j = rand() % (i + 1);
    std::swap(vec[i], vec[j]);
  }
  before_start_node.next = nodes[vec[0]];
  for (size_t i = 0; i < _size - 1; ++i) {
    nodes[vec[i]]->next = nodes[vec[i + 1]];
  }
  nodes[vec[_size - 1]]->next = nullptr;
}
