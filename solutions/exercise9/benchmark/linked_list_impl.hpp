#include "linked_list.hpp"
#include <stdexcept>

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
LinkedList<T>::iterator
LinkedList<T>::iterator::operator+(unsigned int n)
{
  LinkedListNode<T>* current_node = this->ptr;
  while (current_node != nullptr && n > 0) {
    current_node = current_node->next;
    --n;
  }
  return iterator(current_node);
}

template<class T>
bool
LinkedList<T>::iterator::operator!=(const iterator& other)
{
  return this->ptr != other.ptr;
}

template<class T>
T&
LinkedList<T>::operator[](size_t pos)
{
  if (__size <= pos)
    throw std::out_of_range("Access Element out of Bounds");
  LinkedListNode<T>* currentNode = head;
  for (size_t i = 0; i < pos; ++i) {
    currentNode = currentNode->next;
  }
  return currentNode->value;
}

template<class T>
LinkedList<T>::iterator
LinkedList<T>::begin()
{
  return iterator(head);
}

template<class T>
LinkedList<T>::iterator
LinkedList<T>::end()
{
  return iterator(nullptr);
}

template<class T>
LinkedList<T>::iterator
LinkedList<T>::insert(iterator pos, const T& value)
{
  LinkedListNode<T>* new_node = new LinkedListNode<T>();
  new_node->value = value;
  LinkedListNode<T>* prev_node = pos.ptr;
  if (head == nullptr) { // insert into empty list
    head = new_node;
    new_node->next = nullptr;
    ++__size;
    return iterator(head);
  } else if (prev_node == head) { // insert at pos 0
    new_node->next = prev_node;
    head = new_node;
    ++__size;
    return iterator(head);
  }
  LinkedListNode<T>* current_node = head;
  while (current_node->next != prev_node) {
    current_node = current_node->next;
  }
  current_node->next = new_node;
  new_node->next = prev_node;
  ++__size;
  return iterator(new_node);
}

template<class T>
LinkedList<T>::iterator
LinkedList<T>::erase(iterator pos)
{
  LinkedListNode<T>* node_to_delete = pos.ptr;
  if (node_to_delete == nullptr)
    return iterator(nullptr);
  if (node_to_delete == head) {
    head = node_to_delete->next;
    delete node_to_delete;
    __size--;
    return iterator(head);
  }
  LinkedListNode<T>* current_node = head;
  while (current_node->next != node_to_delete) {
    current_node = current_node->next;
  }
  current_node->next = node_to_delete->next;
  delete node_to_delete;
  --__size;
  return iterator(current_node->next);
}

template<class T>
size_t
LinkedList<T>::size()
{
  return __size;
}
