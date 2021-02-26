import '../styles/table.scss'

window.addEventListener('load', () => {
  const table = document.querySelector('.lawsuits-table-plugin')
  const rows = document.querySelectorAll('.lawsuits-table-plugin tr.lawsuit-table-item')


  for (const row of Array.from(rows)) {
    row.addEventListener('click', (e) => {
      e.preventDefault()
      toggleRow(row)

      // set hash without scrolling
      window.history.pushState(undefined, undefined, '#' + row.getAttribute('id'))
    })
  }

  // check for permalink #klage-detail-$n
  const [, pk] = /#klage-detail-(\d+)/.exec(window.location.hash) ?? []
  if (pk) {
    const row = table.querySelector(`tr[data-pk="${pk}"]`)
    if (row) {
      row.scrollIntoView()
      toggleRow(row)
    }
  }
})

function toggleRow(row) {
  const title = row.querySelector('.lawsuit-table-item-title')
  const icon = title.querySelector('i.fa')
  const isActive = row.classList.contains('active')
  
  row.classList.toggle('active')
  icon.classList.toggle('fa-chevron-up')
  icon.classList.toggle('fa-chevron-down')

  title.setAttribute('colspan', isActive ? '1' : '4')
}