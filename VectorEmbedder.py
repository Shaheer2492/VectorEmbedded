import openai
import gspread
import pinecone
from oauth2client.service_account import ServiceAccountCredentials


def generate_query(dictionary):
  # Extract the values from the dictionary and remove the leading and trailing spaces
  values = [v.strip() for v in dictionary.values()]
  # Join the values together into a single string with commas between them and a period at the end
  sentence = ', '.join(values) + '.'
  return sentence


# use creds to create a client to interact with the Google Drive API
scope = [
  'https://spreadsheets.google.com/feeds',
  'https://www.googleapis.com/auth/drive'
]
creds = ServiceAccountCredentials.from_json_keyfile_name('keys.json', scope)
client = gspread.authorize(creds)
sheet = client.open("SessionAi").sheet1
# Extract all of the values
list_of_hashes = sheet.get_all_records()
header_row = sheet.row_values(1) 
row_id_index = header_row.index("Row ID")
# Initialize a dictionary to hold column data
data_dict = {
  rec['Email']: str(rec)
  for rec in list_of_hashes if rec['Status'] == 'TRUE'
}

openai.api_key = "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"
openai.Engine.list()  # check we have authenticated
MODEL = "text-embedding-ada-002"

# Create embeddings for each individual and upsert to Pinecone index
pinecone.init(api_key="d2941534-f630-4791-b08a-80d5fa944aac",
              environment="asia-southeast1-gcp-free")
if 'openai' not in pinecone.list_indexes():
  pinecone.create_index(
    'openai', dimension=1536)  # Assume 1536 as the dimension of the embeddings
index = pinecone.Index('openai')

to_upsert = []
for email, data in data_dict.items():
  res = openai.Embedding.create(input=data, engine=MODEL)
  embeds = [record['embedding'] for record in res['data']]
  # Extract individual fields from each record
  fields = data.split(',')  # Assuming that fields are separated by tabs
  metadata = {
    '1': fields[0],
    '2': fields[1],
    '3': fields[2],
    '4': fields[3],
    '5': fields[4],
    '6': fields[5],
    '7': fields[6],
    '8': fields[7],
    '9': fields[8]
  }
  to_upsert.append((email, embeds[0], metadata))
index.upsert(vectors=to_upsert)
# Assuming your spreadsheet has a worksheet named "output" where you want to write the data
output_sheet = client.open("SessionAi").worksheet("Hackers")
name_column_index = row_id_index + 1
email_column_index = name_column_index + 1
for record in list((list_of_hashes)):
  query = generate_query(record)
  xq = openai.Embedding.create(input=query,
                               engine=MODEL)['data'][0]['embedding']
  # get the row id of the query user
  query_row_id = record['Row ID']

  # query, returning the top 5 most similar results
  res = index.query(
    [xq], top_k=4, include_metadata=True
  )  # increase top_k to 6 because we may discard some results

  # get the email id of the query user
  query_email_id = record['Email']
  names = []
  emails = []
  row_count = 2
  for match in res['matches']:
    # generate the query for the match
    name = generate_query(match['metadata'])
    email = match['id']
    
    names.append(name)
    emails.append(email)

  # Increase the row count
  row_count += 1
  data_to_write = [[name, email] for name, email in zip(names, emails)]
  cell_list = output_sheet.range(
    f'{gspread.utils.rowcol_to_a1(2, name_column_index)}:{gspread.utils.rowcol_to_a1(row_count, email_column_index)}'
  )
  for i, cell in enumerate(cell_list[::2]):  # Write names
    cell.value = data_to_write[i][0]
  for i, cell in enumerate(cell_list[1::2]):  # Write emails
    cell.value = data_to_write[i][1]
  output_sheet.update_cells(cell_list)

print("Done.")
