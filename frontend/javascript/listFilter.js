window.addEventListener('load', () => {
  const listFilters = document.querySelectorAll('.list-filter__search')
  for (const filterInput of Array.from(listFilters)) {
    const list = filterInput.parentElement.querySelector('ul')
    filterInput.addEventListener('input', (e) => {
      const filterValue = e.target.value
      filterList(list, filterValue)
    })
  }
})

function filterList(list, value) {
  const listEntries = list.querySelectorAll('li')
  for (const entry of Array.from(listEntries)) {
    if (entry.querySelector('a').text.includes(value)) {
      entry.style.display = ''
    } else {
      entry.style.display = 'none'
    }
  }
}
