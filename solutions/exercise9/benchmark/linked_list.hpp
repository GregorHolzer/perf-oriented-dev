#pragma once
#include <cstddef>

template<class T>
class LinkedList;

template<class T>
class LinkedListNode
{
  friend class LinkedList<T>;

private:
  LinkedListNode* next = nullptr;
  T value;
};

template<class T>
class LinkedList
{
public:
  class iterator
  {
    friend class LinkedList<T>;

  public:
    iterator(LinkedListNode<T>* ptr);
    T& operator*();
    iterator& operator++();
    bool operator!=(const iterator& other);

  private:
    LinkedListNode<T>* ptr;
  };

  ~LinkedList();

  iterator begin();
  iterator end();
  iterator before_begin();

  size_t size();

  iterator insert_after(iterator pos, const T& value);
  iterator erase_after(iterator pos);

  void shuffle_list(int);

private:
  LinkedListNode<T> before_start_node = LinkedListNode<T>();
  size_t _size = 0;
};

#include "linked_list_impl.hpp"
