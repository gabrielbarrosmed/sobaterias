"""
Cria as tags de conversão do Google Ads no GTM para WhatsApp e Telefone.
"""
import os
import sys
import json
import asyncio

# Adiciona o caminho do mcp-for-gtm para importar o GTMClient
sys.path.insert(0, r'C:\Projetos Claude\mcp-for-gtm')

from gtm_client import GTMClient

CREDENTIALS_FILE = r'C:\Projetos Claude\mcp-for-gtm\credentials.json'
TOKEN_FILE       = r'C:\Projetos Claude\mcp-for-gtm\token.json'
GTM_PUBLIC_ID    = 'GTM-KGMD5DZ5'

WHATSAPP_LABEL = 'OYqMCJbA15IcELe4kqAD'
TELEFONE_LABEL = 'TXIGCMqaz5IcELe4kqAD'
CONVERSION_ID  = '872717367'


async def find_container(client):
    """Encontra account_id e container_id pelo public ID."""
    accounts = client.service.accounts().list().execute()
    for account in accounts.get('account', []):
        account_id = account['accountId']
        containers = await client.list_containers(account_id)
        for container in containers:
            if container.get('publicId') == GTM_PUBLIC_ID:
                return account_id, container['containerId']
    raise Exception(f'Container {GTM_PUBLIC_ID} não encontrado.')


async def get_workspace_id(client, account_id, container_id):
    """Retorna o ID do workspace padrão."""
    parent = f'accounts/{account_id}/containers/{container_id}'
    result = client.service.accounts().containers().workspaces().list(parent=parent).execute()
    workspaces = result.get('workspace', [])
    if not workspaces:
        raise Exception('Nenhum workspace encontrado.')
    # Usa o workspace padrão (geralmente o primeiro)
    return workspaces[0]['workspaceId']


async def get_trigger_ids(client, account_id, container_id, workspace_id):
    """Busca os trigger IDs de WhatsApp e Telefone já existentes."""
    parent = f'accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}'
    result = client.service.accounts().containers().workspaces().triggers().list(parent=parent).execute()
    triggers = result.get('trigger', [])

    wa_id = None
    tel_id = None
    for t in triggers:
        name = t.get('name', '')
        if 'WhatsApp' in name or 'whatsapp' in name.lower():
            wa_id = t['triggerId']
            print(f'  Trigger WhatsApp encontrado: {name} (id={wa_id})')
        elif 'Ligar' in name or 'Telefone' in name or 'tel' in name.lower():
            tel_id = t['triggerId']
            print(f'  Trigger Telefone encontrado: {name} (id={tel_id})')

    return wa_id, tel_id


async def create_conversion_tag(client, account_id, container_id, workspace_id, name, label, trigger_id):
    """Cria uma tag de conversão do Google Ads."""
    parent = f'accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}'

    tag_body = {
        'name': name,
        'type': 'awct',
        'parameter': [
            {'type': 'template', 'key': 'conversionId',    'value': CONVERSION_ID},
            {'type': 'template', 'key': 'conversionLabel', 'value': label},
            {'type': 'template', 'key': 'currencyCode',    'value': 'BRL'},
        ],
        'firingTriggerId': [trigger_id],
        'tagFiringOption': 'ONCE_PER_EVENT',
    }

    result = client.service.accounts().containers().workspaces().tags().create(
        parent=parent,
        body=tag_body
    ).execute()

    print(f'  Tag criada: {result["name"]} (id={result["tagId"]})')
    return result


async def publish(client, account_id, container_id, workspace_id):
    """Cria versão e publica."""
    parent = f'accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}'

    version_result = client.service.accounts().containers().workspaces().create_version(
        path=parent,
        body={
            'name': 'Conversões Google Ads - WhatsApp e Telefone',
            'notes': 'Tags de conversão criadas automaticamente via script.'
        }
    ).execute()

    version_path = version_result['containerVersion']['path']

    publish_result = client.service.accounts().containers().versions().publish(
        path=version_path
    ).execute()

    print(f'  Publicado: {version_path}')
    return publish_result


async def main():
    print('Conectando ao GTM...')
    client = GTMClient(credentials_file=CREDENTIALS_FILE, token_file=TOKEN_FILE)

    print(f'Buscando container {GTM_PUBLIC_ID}...')
    account_id, container_id = await find_container(client)
    print(f'  account_id={account_id}  container_id={container_id}')

    print('Buscando workspace...')
    workspace_id = await get_workspace_id(client, account_id, container_id)
    print(f'  workspace_id={workspace_id}')

    print('Buscando triggers existentes...')
    wa_trigger_id, tel_trigger_id = await get_trigger_ids(client, account_id, container_id, workspace_id)

    if not wa_trigger_id or not tel_trigger_id:
        print('ERRO: Triggers não encontrados. Verifique o GTM.')
        return

    print('Criando tags de conversão...')
    await create_conversion_tag(
        client, account_id, container_id, workspace_id,
        name='Google Ads - Conversão - WhatsApp Click',
        label=WHATSAPP_LABEL,
        trigger_id=wa_trigger_id
    )
    await create_conversion_tag(
        client, account_id, container_id, workspace_id,
        name='Google Ads - Conversão - Telefone Click',
        label=TELEFONE_LABEL,
        trigger_id=tel_trigger_id
    )

    print('Publicando container...')
    await publish(client, account_id, container_id, workspace_id)

    print('\nConcluído! As conversões estão ativas no GTM.')


if __name__ == '__main__':
    asyncio.run(main())
