import '../styles/table.scss'

window.addEventListener('load', () => {
  const table = document.querySelector('.lawsuits-table-plugin')
  const rows = table.querySelectorAll('tr.lawsuit-table-item')


  for (const row of Array.from(rows)) {
    row.addEventListener('click', (e) => {
      e.preventDefault()
      toggleRow(row)

      // set hash without scrolling
      window.history.pushState(undefined, undefined, '#' + row.getAttribute('id'))
    })
  }

  // filters
  const [search, status, court] = ['search', 'status', 'court'].map(id => {
    const el = document.querySelector(`#lawsuits-${id}`)
    el.addEventListener('input', updateFilters)
    return el
  })

  function updateFilters() { 
    const searchText = search.value.toLowerCase()
    const statusValue = status.value
    const courtValue = court.value

    let foundNone = true
    
    for (const row of rows) {
      if (isRowActive(row)) toggleRow(row)
      const title = row.querySelector('.lawsuit-table-item-title').innerText.toLowerCase()
      const reference = row.dataset.reference.toLowerCase()

      let show = true

      if (statusValue !== 'all' && row.dataset.status !== statusValue) {
        show = false
      }

      if (courtValue !== 'all' && row.dataset.court !== courtValue) {
        show = false
      }

      const found = title.includes(searchText) || reference.includes(searchText)
      if (searchText.length > 2 && !found) {
        show = false
      }

      if (show) {
        row.classList.remove('d-none')
        foundNone = false
      } else {
        row.classList.add('d-none')
      }
    }

    const foundNoneEl = table.querySelector('.lawsuit-table-none')
    if (foundNone) {
      foundNoneEl.classList.remove('d-none')
    } else {
      foundNoneEl.classList.add('d-none')
    }
  }


  function toggleById(id = window.location.hash) {
    const [, pk] = /klage-detail-(\d+)/.exec(id) ?? []
    if (pk) {
      const row = table.querySelector(`tr[data-pk="${pk}"]`)
      row.scrollIntoView()
      if (row && !isRowActive(row)) {
        toggleRow(row)
      }
    }
  }
  toggleById()

  document.querySelectorAll('a[data-toggle-row]').forEach(el => {
    el.addEventListener('click', e => {
      toggleById(e.target.hash)
    })
  })
})

const isRowActive = row => row.classList.contains('active')

function toggleRow(row) {
  const title = row.querySelector('.lawsuit-table-item-title')
  const icon = title.querySelector('i.fa')
  const isActive = isRowActive(row)
  
  row.classList.toggle('active')
  icon.classList.toggle('fa-chevron-up')
  icon.classList.toggle('fa-chevron-down')

  title.setAttribute('colspan', isActive ? '1' : '3')
}